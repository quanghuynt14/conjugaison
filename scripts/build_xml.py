#!/usr/bin/env python3
"""data/verbs.json -> src/conjugaison.xml, la source que compile le Dictionary Development Kit.

Une entrée par **forme**, tous verbes confondus. Chercher « vis » ouvre une seule
page qui dit d'abord ce que « vis » peut être — passé simple de voir, présent de
vivre, impératif de vivre — puis déroule la conjugaison des deux verbes.

C'est une conjugaison inversée, et c'est ce qui décide du découpage. Une entrée
par verbe rendrait le même corps pour ses quarante clés : le haut de la page ne
peut pas savoir quelle forme vous avez tapée. Une entrée par forme le sait, et
c'est la seule chose qu'on lui demande.

Une forme peut avoir plusieurs analyses dans un même verbe et dans un même mode :
« dis » est le présent *et* le passé simple de dire. On ne choisit jamais, on les
liste toutes, dans l'ordre fixe de PLAN.

Les temps composés ne sont pas stockés. Ils sont construits depuis l'auxiliaire
conjugué et le participe passé, parce que c'est ce qu'un temps composé est. Ils
ne sont pas indexés non plus : « ai fait » fait deux mots, et d:value n'accepte
pas l'espace.

Mais ils sont *cités*. « j’ai vécu » nomme deux formes cherchables, « ai » et
« vécu » ; chacune reçoit sa ligne dans le tableau de l'autre. Sans quoi
chercher « vécu » répondait « participe passé » et s'arrêtait là — vrai, et
muet sur les quarante-cinq cases où la forme travaille. Aucune clé nouvelle
n'en sort : on ajoute des lignes, pas des entrées.
"""

import collections
import hashlib
import json
import pathlib
import re
import sys
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "verbs.json"
OUT = ROOT / "src" / "conjugaison.xml"

# --- accords et sujets ------------------------------------------------------

SUBJECTS = ["je", "tu", "il", "nous", "vous", "ils"]

# Ce que porte la dernière colonne. Un verbe conjugué s'accorde avec son sujet
# en personne et en nombre ; un participe passé, en genre et en nombre. Deux
# façons de s'accorder, une seule colonne — d'où « accord » plutôt que
# « personne », qu'un participe n'a pas.
ACCORDS_FINITE = [
    "1ʳᵉ du singulier", "2ᵉ du singulier", "3ᵉ du singulier",
    "1ʳᵉ du pluriel", "2ᵉ du pluriel", "3ᵉ du pluriel",
]
# L'impératif n'a que trois cases, et elles ne sont pas les trois premières.
ACCORDS_IMPER = ["2ᵉ du singulier", "1ʳᵉ du pluriel", "2ᵉ du pluriel"]
ACCORDS_PARTICIPE = [
    "masculin singulier", "féminin singulier",
    "masculin pluriel", "féminin pluriel",
]

# --- les temps --------------------------------------------------------------

# mode -> [(clé, libellé, nature, source)]
#   "simple"  : formes lues telles quelles dans verbs.json
#   "compose" : auxiliaire conjugué à `source`, puis le participe passé
PLAN = [
    ("Indicatif", [
        ("ind.pres",    "Présent",           "simple",  "ind.pres"),
        ("ind.pc",      "Passé composé",     "compose", "ind.pres"),
        ("ind.imp",     "Imparfait",         "simple",  "ind.imp"),
        ("ind.pqp",     "Plus-que-parfait",  "compose", "ind.imp"),
        ("ind.ps",      "Passé simple",      "simple",  "ind.ps"),
        ("ind.pa",      "Passé antérieur",   "compose", "ind.ps"),
        ("ind.fut",     "Futur simple",      "simple",  "ind.fut"),
        ("ind.fa",      "Futur antérieur",   "compose", "ind.fut"),
    ]),
    ("Conditionnel", [
        ("cond.pres",   "Présent",           "simple",  "cond.pres"),
        ("cond.passe",  "Passé",             "compose", "cond.pres"),
    ]),
    ("Subjonctif", [
        ("subj.pres",   "Présent",           "simple",  "subj.pres"),
        ("subj.passe",  "Passé",             "compose", "subj.pres"),
        ("subj.imp",    "Imparfait",         "simple",  "subj.imp"),
        ("subj.pqp",    "Plus-que-parfait",  "compose", "subj.imp"),
    ]),
    ("Impératif", [
        ("imper.pres",  "Présent",           "simple",  "imper.pres"),
        ("imper.passe", "Passé",             "compose", "imper.pres"),
    ]),
]

MODE_OF = {key: mode for mode, tenses in PLAN for key, _, _, _ in tenses}
LABEL_OF = {key: label for _, tenses in PLAN for key, label, _, _ in tenses}

# Les formes non conjuguées, après les temps, dans cet ordre. L'infinitif et le
# participe sont des modes au même titre que l'indicatif, et le libellé le dit
# comme ailleurs : mode puis temps. « Infinitif » seul était le seul des dix-neuf
# à s'arrêter au mode.
NONFINITE = [
    ("inf",        "Infinitif présent"),
    ("part.pres",  "Participe présent"),
    ("part.passe", "Participe passé"),
]

# Les colonnes du tableau inversé. Le verbe n'y est pas : il est en légende,
# une fois par tableau. verify_lookup.py s'en sert pour reconnaître un tableau
# dans le texte brut que rend Dictionary.app.
#
# L'accord n'y est pas non plus. Il est déterminé par les deux autres colonnes —
# aucune paire (conjugaison, temps) ne se répète dans un tableau — donc il ne
# distinguait aucune ligne d'aucune autre ; il nommait. Et il nommait ce que la
# ligne montrait déjà : « je vis » suivi de « 1ʳᵉ du singulier », 504 fois sur
# 564. Les 52 autres — impératif, participe — portent la marque dans la forme :
# le -ez de « vivez », le -e de « vécue ». La colonne reste dans `Analysis`,
# où verify_lookup.py l'imprime pour rendre son contrôle lisible.
REVERSE_COLUMNS = ("conjugaison", "temps")

# Les temps construits. Une ligne portant l'un d'eux dit où la forme apparaît,
# pas ce qu'elle est — et le tableau les range après, d'où ce jeu.
COMPOSED = {key for _, tenses in PLAN for key, _, kind, _ in tenses
            if kind == "compose"}

# L'ordre du tableau inversé : tous les temps dans l'ordre de PLAN, composés
# compris, puis les formes non conjuguées.
SLOT_ORDER = (
    [key for _, tenses in PLAN for key, _, _, _ in tenses]
    + [key for key, _ in NONFINITE]
)
SLOT_RANK = {key: i for i, key in enumerate(SLOT_ORDER)}


def tense_label(key):
    """« Indicatif passé simple », « Impératif présent », « Participe passé »."""
    if key in dict(NONFINITE):
        return dict(NONFINITE)[key]
    return f"{MODE_OF[key]} {LABEL_OF[key].lower()}"


# --- élision ----------------------------------------------------------------

VOWELS = "aeiouàâäéèêëîïôöùûüy"
ELIDABLE = {"je", "que"}


def elide(left, right):
    """« que » + « il » -> « qu’il ».

    Le h aspiré n'est pas traité : aucun verbe français n'a de forme conjuguée
    qui en commence une. Les noms en ont, pas les verbes.
    """
    head = right.split(" ", 1)[0]
    if left in ELIDABLE and head and head[0].lower() in VOWELS + "h":
        return left[:-1] + "’" + right
    return left + " " + right


def subject_for(tense_key, i):
    """Le sujet nu. L'impératif n'en a pas."""
    if tense_key.startswith("imper."):
        return None
    return SUBJECTS[i]


def with_subject(tense_key, i, form):
    """« aie vécu » -> « que j’aie vécu ».

    L'élision se fait de droite à gauche : « je » se colle d'abord au verbe,
    « que » se colle ensuite au résultat. Dans l'autre sens on obtient
    « que je aie vécu », parce que « que je » n'est plus un mot élidable.
    """
    subject = subject_for(tense_key, i)
    if subject is None:
        return form
    cell = elide(subject, form)
    return elide("que", cell) if tense_key.startswith("subj.") else cell


# --- conjugaison ------------------------------------------------------------


def cells_for(verb, aux, key, kind, source):
    """Les six (ou trois) cases d'un temps, sujet attaché."""
    if kind == "simple":
        raw = verb["tenses"][source]
    else:
        raw = [f"{a} {verb['participe_passe'][0]}" for a in aux["tenses"][source]]

    return [with_subject(key, i, form) for i, form in enumerate(raw)]


Analysis = collections.namedtuple(
    "Analysis", "verb slot slot_index conjugated accord"
)


def analyses_of(verb, aux):
    """forme -> [Analysis], pour ce verbe seul.

    Toutes les analyses, jamais la première seulement. « dis » est le présent et
    le passé simple de dire ; n'en garder qu'une afficherait un fait faux.
    """
    found = collections.defaultdict(list)

    def record(form, slot, i, conjugated, accord):
        found[form].append(Analysis(verb, slot, i, conjugated, accord))

    for _, tenses in PLAN:
        for key, _, kind, source in tenses:
            if kind != "simple":
                continue
            accords = ACCORDS_IMPER if key.startswith("imper.") else ACCORDS_FINITE
            conjugated = cells_for(verb, aux, key, kind, source)
            for i, form in enumerate(verb["tenses"][source]):
                record(form, key, i, conjugated[i], accords[i])

    record(verb["infinitif"], "inf", 0, verb["infinitif"], "")
    record(verb["participe_present"], "part.pres", 0, verb["participe_present"], "")
    for i, form in enumerate(verb["participe_passe"]):
        record(form, "part.passe", i, form, ACCORDS_PARTICIPE[i])

    return found


def occurrences_of(verb, aux, keys):
    """forme -> [Analysis], pour les cases composées de ce verbe.

    « j’ai vécu » cite « ai » et « vécu ». On découpe la case en mots et on
    garde ceux qui sont des clés du dictionnaire ; le reste — les sujets, le
    « que » du subjonctif — n'est cherchable nulle part et ne produit rien.

    Une case ne donne qu'une ligne par forme, d'où l'ensemble : c'est ce qui
    garantit qu'une ligne du tableau vaut une case surlignée, et pas deux.
    """
    found = collections.defaultdict(list)
    for _, tenses in PLAN:
        for key, _, kind, source in tenses:
            if kind != "compose":
                continue
            accords = ACCORDS_IMPER if key.startswith("imper.") else ACCORDS_FINITE
            for i, cell in enumerate(cells_for(verb, aux, key, kind, source)):
                for form in sorted(set(re.findall(r"\w+", cell)) & keys):
                    found[form].append(Analysis(verb, key, i, cell, accords[i]))
    return found


# --- xml --------------------------------------------------------------------


def esc(text):
    return (text.replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace('"', "&quot;"))


def slug(form):
    """Un id XML sûr et stable. L'ASCII seul se collisionne — « ou » et « où »
    donnent le même — d'où le condensat, qui les sépare."""
    plain = "".join(
        c for c in unicodedata.normalize("NFD", form.lower())
        if c.isascii() and c.isalnum()
    )
    digest = hashlib.md5(form.encode("utf-8")).hexdigest()[:6]
    return f"{plain or 'x'}_{digest}"


def anchor_id(verb_id, key):
    return f"{verb_id}_{key.replace('.', '-')}"


def render_table(verb, aux, matches):
    """La conjugaison complète d'un verbe. `matches` = {(clé, index)} à surligner."""
    vid = verb["id"]
    out = [f'    <div class="verb" id="{anchor_id(vid, "table")}">']
    out.append(f'      <h2 class="lemma">{esc(verb["infinitif"])}</h2>')
    out.append(
        f'      <div class="meta">{esc(verb["groupe"])} · auxiliaire '
        f'<i>{esc(verb["auxiliaire"])}</i></div>'
    )

    out.append('      <div class="nonfinite">')
    for key, label in NONFINITE:
        if key == "inf":
            forms = [verb["infinitif"]]
        elif key == "part.pres":
            forms = [verb["participe_present"]]
        else:
            forms = verb["participe_passe"]
        # Le participe passé a quatre cases comme un temps en a six, et
        # `matches` les distingue déjà. Surligner la ligne entière dirait que
        # « vécu » est aussi « vécue » : on marque la case, pas la ligne.
        cells = ", ".join(
            f'<span class="nf-cell'
            f'{" cell-match" if (key, i) in matches else ""}">{esc(form)}</span>'
            for i, form in enumerate(forms)
        )
        out.append(
            f'        <div class="nf-row" id="{anchor_id(vid, key)}">'
            f'<span class="nf-label">{esc(label.lower())}</span>'
            f'<span class="form">{cells}</span></div>'
        )
    out.append("      </div>")

    for mode, tenses in PLAN:
        out.append('      <div class="mode">')
        out.append(f'        <h3>{esc(mode)}</h3>')
        for key, label, kind, source in tenses:
            out.append(f'        <div class="tense" id="{anchor_id(vid, key)}">')
            out.append(f'          <h4>{esc(label)}</h4>')
            out.append('          <ul class="cells">')
            for i, cell in enumerate(cells_for(verb, aux, key, kind, source)):
                cls = ' class="cell-match"' if (key, i) in matches else ""
                out.append(f'            <li{cls}>{esc(cell)}</li>')
            out.append("          </ul>")
            out.append("        </div>")
        out.append("      </div>")

    if verb.get("note"):
        out.append(f'      <div class="note">{esc(verb["note"])}</div>')
    out.append("    </div>")
    return out


def group_by_verb(records):
    """[(verb, [Analysis])], verbes alphabétiques, ordre des lignes préservé."""
    grouped = collections.defaultdict(list)
    for r in records:
        grouped[r.verb["id"]].append(r)
    return [(rs[0].verb, rs) for _, rs in
            sorted(grouped.items(), key=lambda kv: kv[1][0].verb["infinitif"])]


def render_reverse(verb, records):
    """Le tableau inversé d'un seul verbe. « vis » en a deux, vivre et voir.

    Le verbe passe en légende. En colonne il répétait le même mot sur toutes les
    lignes du groupe — quarante-six fois pour « vécu » — et il n'y disait rien
    que le groupe ne dise déjà. Reste ce qui varie d'une ligne à l'autre.
    """
    out = [
        '    <table class="reverse">',
        f'      <caption>{esc(verb["infinitif"])}</caption>',
        "      <tr>" + "".join(f"<th>{c}</th>" for c in REVERSE_COLUMNS) + "</tr>",
    ]
    # Dans le tableau, l'ordre des temps de PLAN. Les lignes qui disent ce que
    # la forme *est* n'y sont donc pas groupées : « Participe passé » vient
    # après les composés qui le citent. La graisse les distingue — la
    # conjugaison la garde sur une ligne directe, la perd sur une ligne citée.
    for r in records:
        cls = ' class="row-cited"' if r.slot in COMPOSED else ""
        out.append(
            f'      <tr{cls}><td class="c-form">{esc(r.conjugated)}</td>'
            f'<td class="c-tense">{esc(tense_label(r.slot))}</td></tr>'
        )
    out.append("    </table>")
    return out


def render_entry(form, records, verbs, auxiliaries):
    """Une entrée : un tableau inversé par verbe, puis leurs conjugaisons.

    Les deux moitiés de la page listent les mêmes verbes dans le même ordre.
    """
    out = [
        f'<d:entry id="f_{slug(form)}" d:title="{esc(form)}">',
        f'  <d:index d:value="{esc(form)}" d:title="{esc(form)}"/>',
        '  <div class="form-entry">',
        f'    <h1 class="searched">{esc(form)}</h1>',
    ]

    groups = group_by_verb(records)
    for verb, rows in groups:
        out += render_reverse(verb, rows)
    for verb, rows in groups:
        matches = {(r.slot, r.slot_index) for r in rows}
        out += render_table(verb, auxiliaries[verb["id"]], matches)

    out.append("  </div>")
    out.append("</d:entry>")
    return "\n".join(out)


def build_index(data):
    """forme -> [Analysis] triées. Le cœur du générateur, isolé pour que
    verify_lookup.py puisse comparer le bundle compilé à ce qu'on a voulu."""
    verbs = {v["id"]: v for v in data["verbs"]}

    auxiliaries = {}
    for verb in data["verbs"]:
        aux = verbs.get(verb["auxiliaire"])
        if aux is None:
            sys.exit(
                f"{verb['id']} : auxiliaire « {verb['auxiliaire']} » absent de "
                "verbs.json. Les temps composés ne se construisent pas sans lui."
            )
        auxiliaries[verb["id"]] = aux

    index = collections.defaultdict(list)
    for verb in data["verbs"]:
        for form, records in analyses_of(verb, auxiliaries[verb["id"]]).items():
            index[form] += records

    # Les composés se lisent après coup : il faut la liste complète des clés
    # pour savoir quels mots d'une case sont cherchables. Elle est close ici —
    # une case composée ne cite que des formes déjà indexées, donc cette
    # seconde passe n'ajoute jamais de clé.
    keys = set(index)
    for verb in data["verbs"]:
        for form, records in occurrences_of(verb, auxiliaries[verb["id"]], keys).items():
            index[form] += records

    # Par verbe (alphabétique), puis par temps dans l'ordre de PLAN — donc par
    # mode, puis par temps dans le mode : Indicatif présent, Indicatif passé
    # composé, Indicatif imparfait… — puis par accord.
    #
    # Le verbe vient en premier parce qu'il découpe la page : un tableau par
    # verbe, et dans chacun l'ordre des temps. C'est aussi l'ordre des
    # conjugaisons du bas. Déterministe, donc check.py peut l'affirmer.
    for records in index.values():
        records.sort(key=lambda r: (r.verb["infinitif"], SLOT_RANK[r.slot],
                                    r.slot_index))
    return index, verbs, auxiliaries


def load():
    return json.loads(SRC.read_text(encoding="utf-8"))


def main():
    data = load()
    index, verbs, auxiliaries = build_index(data)

    body = [render_entry(form, index[form], verbs, auxiliaries)
            for form in sorted(index)]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<d:dictionary xmlns="http://www.w3.org/1999/xhtml"'
        ' xmlns:d="http://www.apple.com/DTDs/DictionaryService-1.0.rng">\n'
        + "\n".join(body) + "\n</d:dictionary>\n",
        encoding="utf-8",
    )

    rows = sum(len(r) for r in index.values())
    print(f"{OUT.relative_to(ROOT)} : {len(data['verbs'])} verbes, "
          f"{len(index)} formes, {rows} analyses")


if __name__ == "__main__":
    main()
