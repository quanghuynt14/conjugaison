#!/usr/bin/env python3
"""Contrôle du XML produit, avant de le donner au compilateur d'Apple.

La panne qu'on cherche n'est pas un XML malformé — xmllint la voit et le build
s'arrête. C'est la forme *absente*, ou l'analyse *fausse* : rien ne les
référence, rien ne s'en plaint, et elles ne se manifestent que le jour où on
lit la page et où elle ment.

Usage :  python3 scripts/check.py [forme…]
"""

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


def rows_of(entry):
    """[(verbe, conjugaison, temps, accord)] du tableau inversé."""
    out = []
    for tr in entry.iter(f"{X}tr"):
        cells = [(td.text or "").strip() for td in tr.findall(f"{X}td")]
        if len(cells) == 4:
            out.append(tuple(cells))
    return out


def main():
    if not XML.exists():
        sys.exit(f"{XML} absent. Lancez d'abord `make xml`.")

    entries = ET.parse(XML).getroot().findall(f"{D}entry")
    problems = []
    seen_values = {}
    seen_ids = {}
    index = {}
    total_rows = 0

    for entry in entries:
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
        index[form] = rows
        total_rows += len(rows)

        if not rows:
            problems.append(f"« {form} » : tableau inversé vide")
            continue

        for verb, conjugated, tense, accord in rows:
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
            if tense not in NONFINITE_LABELS and not accord:
                problems.append(f"« {form} » : {tense} sans accord")

        # L'ordre annoncé : verbe alphabétique, puis temps dans l'ordre de PLAN.
        keys = [(v, RANK_OF_LABEL.get(t, 99)) for v, _, t, _ in rows]
        if keys != sorted(keys):
            problems.append(f"« {form} » : lignes hors de l'ordre annoncé")

        # Un surlignage par analyse, ni plus ni moins. Un fond en trop désigne
        # une case qui n'est pas la bonne, ce qui est un mensonge silencieux.
        finite = sum(1 for _, _, t, _ in rows if t not in NONFINITE_LABELS)
        li_hits = sum(1 for li in entry.iter(f"{X}li")
                      if "cell-match" in (li.get("class") or ""))
        nf_slots = {(v, t) for v, _, t, _ in rows if t in NONFINITE_LABELS}
        nf_hits = sum(1 for s in entry.iter(f"{X}span")
                      if "cell-match" in (s.get("class") or ""))
        if li_hits != finite:
            problems.append(
                f"« {form} » : {li_hits} cases surlignées pour {finite} analyses conjuguées")
        if nf_hits != len(nf_slots):
            problems.append(
                f"« {form} » : {nf_hits} formes non conjuguées surlignées pour "
                f"{len(nf_slots)} attendues")

    print(f"{len(entries)} entrées, {len(seen_values)} clés, {total_rows} analyses")

    for form in sys.argv[1:]:
        rows = index.get(form)
        if rows is None:
            problems.append(f"« {form} » n'a pas d'entrée — introuvable dans Dictionary.app")
            continue
        print(f"  « {form} »")
        for verb, conjugated, tense, accord in rows:
            print(f"      {verb:<8} {conjugated:<18} {tense:<24} {accord}")

    if problems:
        print()
        for problem in problems:
            print(f"  ✗ {problem}")
        sys.exit(1)
    print("  tout se tient")


if __name__ == "__main__":
    main()
