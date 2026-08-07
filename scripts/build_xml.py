#!/usr/bin/env python3
"""data/verbs.json -> src/conjugaison.xml, the source the Dictionary Development Kit compiles.

One <d:entry> per verb, keyed on the infinitive. Every inflected form of that verb
becomes a <d:index> pointing at the same entry, so looking up « fasse » opens
« faire » and scrolls to the subjonctif présent. That is how Apple's own dictionaries
handle inflections, and it is the whole trick: the deck is verbs, the index is forms.

Compound tenses are not stored. They are built here from the auxiliary's simple
tenses plus the past participle, which is what a compound tense *is*. Storing
« j'ai fait » would be storing a fact the grammar already gives you.
"""

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "verbs.json"
OUT = ROOT / "src" / "conjugaison.xml"

# --- display ---------------------------------------------------------------

SUBJECTS = ["je", "tu", "il", "nous", "vous", "ils"]
IMPER_SUBJECTS = [None, None, None]  # l'impératif n'a pas de sujet exprimé

# mode -> [(tense key, label, kind, source)]
#   kind "simple"   : forms read straight from verbs.json
#   kind "compose"  : auxiliary conjugated at `source`, then the past participle
PLAN = [
    ("Indicatif", [
        ("ind.pres",   "Présent",           "simple",  "ind.pres"),
        ("ind.pc",     "Passé composé",     "compose", "ind.pres"),
        ("ind.imp",    "Imparfait",         "simple",  "ind.imp"),
        ("ind.pqp",    "Plus-que-parfait",  "compose", "ind.imp"),
        ("ind.ps",     "Passé simple",      "simple",  "ind.ps"),
        ("ind.pa",     "Passé antérieur",   "compose", "ind.ps"),
        ("ind.fut",    "Futur simple",      "simple",  "ind.fut"),
        ("ind.fa",     "Futur antérieur",   "compose", "ind.fut"),
    ]),
    ("Conditionnel", [
        ("cond.pres",  "Présent",           "simple",  "cond.pres"),
        ("cond.passe", "Passé",             "compose", "cond.pres"),
    ]),
    ("Subjonctif", [
        ("subj.pres",  "Présent",           "simple",  "subj.pres"),
        ("subj.passe", "Passé",             "compose", "subj.pres"),
        ("subj.imp",   "Imparfait",         "simple",  "subj.imp"),
        ("subj.pqp",   "Plus-que-parfait",  "compose", "subj.imp"),
    ]),
    ("Impératif", [
        ("imper.pres", "Présent",           "simple",  "imper.pres"),
        ("imper.passe", "Passé",            "compose", "imper.pres"),
    ]),
]

# Short labels for the search-result list and the "où l'on trouve cette forme" line.
SHORT = {
    "ind.pres": "ind. prés.", "ind.imp": "imparfait", "ind.ps": "passé simple",
    "ind.fut": "futur", "cond.pres": "cond. prés.", "subj.pres": "subj. prés.",
    "subj.imp": "subj. imp.", "imper.pres": "impératif",
    "part.pres": "part. présent", "part.passe": "part. passé", "inf": "infinitif",
}

MODE_OF = {k: mode for mode, tenses in PLAN for k, _, _, _ in tenses}

# --- elision ---------------------------------------------------------------

VOWELS = "aeiouàâäéèêëîïôöùûüy"
ELIDABLE = {"je", "que"}


def elide(left, right):
    """« que » + « il » -> « qu’il ». Assumes no h aspiré; French verb forms
    starting with one are rare enough that the exceptions get a note in the data."""
    head = right.split(" ", 1)[0]
    if left in ELIDABLE and head and head[0].lower() in VOWELS + "h":
        return left[:-1] + "’" + right
    return left + " " + right


def subject_for(tense_key, i):
    if tense_key.startswith("imper."):
        return None
    subj = SUBJECTS[i]
    return elide("que", subj) if tense_key.startswith("subj.") else subj


# --- conjugation -----------------------------------------------------------


def forms_for(verb, aux, key, kind, source):
    """The six (or three) cells of one tense, subject pronoun already attached."""
    if kind == "simple":
        raw = verb["tenses"][source]
    else:
        participle = verb["participe_passe"][0]
        raw = [f"{a} {participle}" for a in aux["tenses"][source]]

    cells = []
    for i, form in enumerate(raw):
        subj = subject_for(key, i)
        cells.append(elide(subj, form) if subj else form)
    return cells


def index_entries(verb):
    """Every distinct searchable form -> the first tense it shows up in.

    Only simple forms are indexed. « ai fait » is two words: not a lookup, and
    d:value is an NMTOKEN anyway. The compound tenses are there to be read.
    """
    seen = {}

    def note(form, tense_key):
        seen.setdefault(form, tense_key)

    note(verb["infinitif"], "inf")
    for mode, tenses in PLAN:
        for key, _, kind, source in tenses:
            if kind != "simple":
                continue
            for form in verb["tenses"][source]:
                note(form, key)
    note(verb["participe_present"], "part.pres")
    for form in verb["participe_passe"]:
        note(form, "part.passe")
    return seen


# --- xml -------------------------------------------------------------------


def esc(text):
    return (text.replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace('"', "&quot;"))


def anchor_id(verb_id, tense_key):
    return f"{verb_id}_{tense_key.replace('.', '-')}"


def render(verb, aux):
    vid = verb["id"]
    out = [f'<d:entry id="v_{esc(vid)}" d:title="{esc(verb["infinitif"])}">']

    for form, tense_key in sorted(index_entries(verb).items()):
        if form == verb["infinitif"]:
            title = form
        else:
            title = f'{form} ({verb["infinitif"]})'
        anchor = f' d:anchor="xpointer(//*[@id=\'{anchor_id(vid, tense_key)}\'])"' \
            if tense_key != "inf" else ""
        out.append(f'  <d:index d:value="{esc(form)}" d:title="{esc(title)}"{anchor}/>')

    out.append('  <div class="verb">')
    out.append(f'    <h1 class="lemma">{esc(verb["infinitif"])}</h1>')
    out.append(
        f'    <div class="meta">verbe · {esc(verb["groupe"])} · auxiliaire '
        f'<i>{esc(verb["auxiliaire"])}</i></div>'
    )

    out.append(f'    <div class="nonfinite" id="{anchor_id(vid, "inf")}">')
    for label, key, value in [
        ("infinitif", "inf", verb["infinitif"]),
        ("participe présent", "part.pres", verb["participe_present"]),
        ("participe passé", "part.passe", ", ".join(verb["participe_passe"])),
    ]:
        out.append(
            f'      <div class="nf-row" id="{anchor_id(vid, key)}">'
            f'<span class="nf-label">{label}</span>'
            f'<span class="form">{esc(value)}</span></div>'
        )
    out.append("    </div>")

    for mode, tenses in PLAN:
        out.append('    <div class="mode">')
        out.append(f'      <h2>{esc(mode)}</h2>')
        for key, label, kind, source in tenses:
            cells = forms_for(verb, aux, key, kind, source)
            out.append(f'      <div class="tense" id="{anchor_id(vid, key)}">')
            out.append(f'        <h3>{esc(label)}</h3>')
            out.append('        <ul class="cells">')
            for cell in cells:
                out.append(f'          <li>{esc(cell)}</li>')
            out.append("        </ul>")
            out.append("      </div>")
        out.append("    </div>")

    if verb.get("note"):
        out.append(f'    <div class="note">{esc(verb["note"])}</div>')

    out.append("  </div>")
    out.append("</d:entry>")
    return "\n".join(out)


def main():
    data = json.loads(SRC.read_text(encoding="utf-8"))
    verbs = {v["id"]: v for v in data["verbs"]}

    body = []
    for verb in data["verbs"]:
        aux = verbs.get(verb["auxiliaire"])
        if aux is None:
            sys.exit(
                f"{verb['id']}: auxiliaire « {verb['auxiliaire']} » absent de verbs.json. "
                "Les temps composés ne peuvent pas être construits sans lui."
            )
        body.append(render(verb, aux))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<d:dictionary xmlns="http://www.w3.org/1999/xhtml"'
        ' xmlns:d="http://www.apple.com/DTDs/DictionaryService-1.0.rng">\n'
        + "\n".join(body)
        + "\n</d:dictionary>\n",
        encoding="utf-8",
    )

    keys = sum(len(index_entries(v)) for v in data["verbs"])
    print(f"{OUT.relative_to(ROOT)} : {len(data['verbs'])} verbes, {keys} formes indexées")


if __name__ == "__main__":
    main()
