#!/usr/bin/env python3
"""Contrôle du XML produit, avant de le donner au compilateur d'Apple.

La panne qu'on cherche n'est pas un XML malformé — xmllint la voit et le build
s'arrête. C'est la forme *absente*, ou l'analyse *fausse* : rien ne les
référence, rien ne s'en plaint, et elles ne se manifestent que le jour où on
lit la page et où elle ment.

Usage :  python3 scripts/check.py [forme…]
"""

import collections
import pathlib
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import build_xml as B  # noqa: E402  — pour SLOT_RANK et tense_label

ROOT = pathlib.Path(__file__).resolve().parent.parent
XML = ROOT / "src" / "conjugaison.xml"
D = "{http://www.apple.com/DTDs/DictionaryService-1.0.rng}"
X = "{http://www.w3.org/1999/xhtml}"

RANK_OF_LABEL = {B.tense_label(k): r for k, r in B.SLOT_RANK.items()}
NONFINITE_LABELS = {label for _, label in B.NONFINITE}
# Les temps construits : la ligne dit où la forme apparaît, pas ce qu'elle est.
CITED_LABELS = {B.tense_label(k) for k in B.COMPOSED}


def rows_of(entry):
    """[(verbe, conjugaison, temps)], tous tableaux inversés confondus.

    Le verbe est en légende et non plus en colonne : il vaut pour tout un
    tableau. On le rattache à chaque ligne pour que les contrôles qui suivent
    n'aient pas à connaître le découpage.
    """
    out = []
    for table in entry.iter(f"{X}table"):
        if "reverse" not in (table.get("class") or ""):
            continue
        caption = table.find(f"{X}caption")
        verb = (caption.text or "").strip() if caption is not None else ""
        for tr in table.iter(f"{X}tr"):
            cells = [(td.text or "").strip() for td in tr.findall(f"{X}td")]
            if len(cells) == len(B.REVERSE_COLUMNS):
                out.append((verb, *cells))
    return out


def captions_of(entry):
    """Les verbes en légende, dans l'ordre des tableaux."""
    return [(t.find(f"{X}caption").text or "").strip()
            for t in entry.iter(f"{X}table")
            if "reverse" in (t.get("class") or "")
            and t.find(f"{X}caption") is not None]


def entries_of(xml):
    """Les entrées, une par une, sans charger le document.

    Le XML pèse un demi-gigaoctet pour mille verbes. `ET.parse` en fait un arbre
    de plusieurs gigaoctets en mémoire, pour un contrôle qui ne regarde jamais
    qu'une entrée à la fois. On la rend, puis on la vide.
    """
    for _, entry in ET.iterparse(xml, events=("end",)):
        if entry.tag != f"{D}entry":
            continue
        yield entry
        entry.clear()


def main():
    if not XML.exists():
        sys.exit(f"{XML} absent. Lancez d'abord `make xml`.")

    wanted = set(sys.argv[1:])
    problems = []
    seen_values = {}
    seen_ids = {}
    index = {}
    total_rows = 0
    total_entries = 0

    for entry in entries_of(XML):
        total_entries += 1
        eid = entry.get("id")
        if eid in seen_ids:
            problems.append(f"id « {eid} » réutilisé — deux entrées se recouvrent")
        seen_ids[eid] = True

        values = [n.get(f"{D}value") for n in entry.findall(f"{D}index")]
        if len(values) != 1:
            problems.append(
                f"{eid} : {len(values)} clés. Une entrée par forme veut dire une "
                "clé par entrée."
            )
        for value in values:
            # L'invariant du découpage par forme : une clé, une seule entrée.
            # Deux, et Dictionary.app affiche deux lignes pour la même recherche.
            if value in seen_values:
                problems.append(
                    f"la clé « {value} » apparaît dans {seen_values[value]} et "
                    f"dans {eid} — la liste de résultats montrera deux lignes"
                )
            seen_values[value] = eid

        form = values[0] if values else eid
        rows = rows_of(entry)
        # On ne garde que ce qu'on va imprimer : tout garder ferait rentrer par
        # la fenêtre la mémoire que la lecture en flux fait sortir par la porte.
        if form in wanted:
            index[form] = rows
        total_rows += len(rows)

        if not rows:
            problems.append(f"« {form} » : tableau inversé vide")
            continue

        for verb, conjugated, tense in rows:
            # La conjugaison affichée doit contenir la forme cherchée. Sinon la
            # ligne parle d'autre chose que de ce qu'on a tapé.
            # Frontière de mot, mais l'apostrophe d'élision en est une : dans
            # « j’ai », la forme « ai » commence bien après le ’.
            if not re.search(rf"(?<!\w){re.escape(form)}(?!\w)", conjugated):
                problems.append(
                    f"« {form} » : la ligne « {conjugated} » ({verb}, {tense}) "
                    "ne contient pas la forme cherchée"
                )
            if tense not in RANK_OF_LABEL:
                problems.append(f"« {form} » : temps inconnu « {tense} »")

        # Ce qui rendait la colonne « accord » supprimable : deux colonnes
        # suffisent à séparer les lignes. Le jour où une paire se répète, la
        # page affiche deux fois la même chose et l'accord manque vraiment.
        vus = collections.Counter(rows)
        for (verb, conjugated, tense), n in vus.items():
            if n > 1:
                problems.append(
                    f"« {form} » : {n} lignes identiques dans le tableau de "
                    f"« {verb} » — {conjugated}, {tense}")

        # L'ordre annoncé : verbe alphabétique, puis temps dans l'ordre de PLAN
        # — mode, puis temps dans le mode. Le verbe découpe la page en tableaux,
        # le temps ordonne chaque tableau.
        keys = [(B.lemma_sort_key(v), RANK_OF_LABEL.get(t, 99))
                for v, _, t in rows]
        if keys != sorted(keys):
            problems.append(f"« {form} » : lignes hors de l'ordre annoncé")

        # Un tableau par verbe, et il se nomme. Une légende vide ou en double
        # veut dire qu'une ligne est rattachée au mauvais verbe — le seul
        # endroit où le verbe est encore écrit.
        captions = captions_of(entry)
        if not all(captions):
            problems.append(f"« {form} » : tableau inversé sans légende")
        if len(captions) != len(set(captions)):
            problems.append(
                f"« {form} » : deux tableaux pour le même verbe — {captions}")
        # « se souvenir » se range à souvenir : le pronom fait partie du nom du
        # verbe, pas de sa place dans l'alphabet.
        if captions != sorted(captions, key=B.lemma_sort_key):
            problems.append(f"« {form} » : tableaux hors de l'ordre alphabétique")

        # Une clé est d'abord une forme. Une entrée qui ne dirait que des cases
        # construites voudrait dire qu'on a indexé un composé.
        if all(t in CITED_LABELS for _, _, t in rows):
            problems.append(
                f"« {form} » : que des lignes citées — une clé doit d'abord "
                "être une forme")

        # Un surlignage par analyse, ni plus ni moins. Un fond en trop désigne
        # une case qui n'est pas la bonne, ce qui est un mensonge silencieux.
        finite = sum(1 for _, _, t in rows if t not in NONFINITE_LABELS)
        li_hits = sum(1 for li in entry.iter(f"{X}li")
                      if "cell-match" in (li.get("class") or ""))
        if li_hits != finite:
            problems.append(
                f"« {form} » : {li_hits} cases surlignées pour {finite} analyses conjuguées")

        # Les cases non conjuguées ne se comptent pas par les lignes : « pris »
        # occupe deux cases de prendre et n'a qu'une ligne. On demande donc
        # directement ce qu'on veut voir — toute case qui montre la forme est
        # marquée, aucune autre ne l'est.
        nf_cells = [s for s in entry.iter(f"{X}span")
                    if "nf-cell" in (s.get("class") or "")]
        montrent = [s for s in nf_cells if re.search(
            rf"(?<!\w){re.escape(form)}(?!\w)", s.text or "")]
        marquees = [s for s in nf_cells if "cell-match" in (s.get("class") or "")]
        if len(marquees) != len(montrent):
            problems.append(
                f"« {form} » : {len(marquees)} formes non conjuguées surlignées "
                f"pour {len(montrent)} qui montrent le mot")

    print(f"{total_entries} entrées, {len(seen_values)} clés, {total_rows} analyses")

    for form in sys.argv[1:]:
        rows = index.get(form)
        if rows is None:
            problems.append(f"« {form} » n'a pas d'entrée — introuvable dans Dictionary.app")
            continue
        print(f"  « {form} »")
        for verb, conjugated, tense in rows:
            print(f"      {verb:<8} {conjugated:<22} {tense}")

    if problems:
        print()
        for problem in problems:
            print(f"  ✗ {problem}")
        sys.exit(1)
    print("  tout se tient")


if __name__ == "__main__":
    main()
