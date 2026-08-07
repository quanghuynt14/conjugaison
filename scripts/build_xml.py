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
"""

import collections
import hashlib
import json
import pathlib
import sys
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "verbs.json"
OUT = ROOT / "src" / "conjugaison.xml"

# --- personnes et sujets ----------------------------------------------------

SUBJECTS = ["je", "tu", "il", "nous", "vous", "ils"]

PERSONS_FINITE = [
    "1ʳᵉ du singulier", "2ᵉ du singulier", "3ᵉ du singulier",
    "1ʳᵉ du pluriel", "2ᵉ du pluriel", "3ᵉ du pluriel",
]
# L'impératif n'a que trois cases, et elles ne sont pas les trois premières.
PERSONS_IMPER = ["2ᵉ du singulier", "1ʳᵉ du pluriel", "2ᵉ du pluriel"]
PERSONS_PARTICIPE = [
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

# Les formes non conjuguées, après les temps, dans cet ordre.
NONFINITE = [
    ("inf",        "Infinitif"),
    ("part.pres",  "Participe présent"),
    ("part.passe", "Participe passé"),
]

# L'ordre du tableau inversé : les temps simples dans l'ordre de PLAN, puis les
# formes non conjuguées. Les composés n'y sont pas — ils ne sont pas indexables.
SLOT_ORDER = (
    [key for _, tenses in PLAN for key, _, kind, _ in tenses if kind == "simple"]
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
    if tense_key.startswith("imper."):
        return None
    subject = SUBJECTS[i]
    return elide("que", subject) if tense_key.startswith("subj.") else subject


# --- conjugaison ------------------------------------------------------------


def cells_for(verb, aux, key, kind, source):
    """Les six (ou trois) cases d'un temps, sujet attaché."""
    if kind == "simple":
        raw = verb["tenses"][source]
    else:
        raw = [f"{a} {verb['participe_passe'][0]}" for a in aux["tenses"][source]]

    out = []
    for i, form in enumerate(raw):
        subject = subject_for(key, i)
        out.append(elide(subject, form) if subject else form)
    return out


Analysis = collections.namedtuple(
    "Analysis", "verb slot person_index conjugated person_label"
)


def analyses_of(verb, aux):
    """forme -> [Analysis], pour ce verbe seul.

    Toutes les analyses, jamais la première seulement. « dis » est le présent et
    le passé simple de dire ; n'en garder qu'une afficherait un fait faux.
    """
    found = collections.defaultdict(list)

    def record(form, slot, i, conjugated, person):
        found[form].append(Analysis(verb, slot, i, conjugated, person))

    for _, tenses in PLAN:
        for key, _, kind, source in tenses:
            if kind != "simple":
                continue
            persons = PERSONS_IMPER if key.startswith("imper.") else PERSONS_FINITE
            conjugated = cells_for(verb, aux, key, kind, source)
            for i, form in enumerate(verb["tenses"][source]):
                record(form, key, i, conjugated[i], persons[i])

    record(verb["infinitif"], "inf", 0, verb["infinitif"], "")
    record(verb["participe_present"], "part.pres", 0, verb["participe_present"], "")
    for i, form in enumerate(verb["participe_passe"]):
        record(form, "part.passe", i, form, PERSONS_PARTICIPE[i])

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
            value = verb["infinitif"]
        elif key == "part.pres":
            value = verb["participe_present"]
        else:
            value = ", ".join(verb["participe_passe"])
        hit = " cell-match" if any(k == key for k, _ in matches) else ""
        out.append(
            f'        <div class="nf-row" id="{anchor_id(vid, key)}">'
            f'<span class="nf-label">{esc(label.lower())}</span>'
            f'<span class="form{hit}">{esc(value)}</span></div>'
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


def render_entry(form, records, verbs, auxiliaries):
    """Une entrée : le tableau inversé, puis la conjugaison de chaque verbe cité."""
    out = [
        f'<d:entry id="f_{slug(form)}" d:title="{esc(form)}">',
        f'  <d:index d:value="{esc(form)}" d:title="{esc(form)}"/>',
        '  <div class="form-entry">',
        f'    <h1 class="searched">{esc(form)}</h1>',
        '    <table class="reverse">',
        "      <tr><th>verbe</th><th>conjugaison</th><th>temps</th>"
        "<th>personne</th></tr>",
    ]
    for r in records:
        out.append(
            f'      <tr><td class="c-verb">{esc(r.verb["infinitif"])}</td>'
            f'<td class="c-form">{esc(r.conjugated)}</td>'
            f'<td class="c-tense">{esc(tense_label(r.slot))}</td>'
            f'<td class="c-person">{esc(r.person_label) or "—"}</td></tr>'
        )
    out.append("    </table>")

    seen = []
    for r in records:
        if r.verb["id"] not in seen:
            seen.append(r.verb["id"])
    for vid in seen:
        verb = verbs[vid]
        matches = {(r.slot, r.person_index) for r in records if r.verb["id"] == vid}
        out += render_table(verb, auxiliaries[vid], matches)

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

    # Par verbe (alphabétique), puis par temps dans l'ordre de PLAN, puis par
    # personne. Déterministe, donc check.py peut l'affirmer.
    for records in index.values():
        records.sort(key=lambda r: (r.verb["infinitif"], SLOT_RANK[r.slot],
                                    r.person_index))
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
