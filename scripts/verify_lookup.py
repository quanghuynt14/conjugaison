#!/usr/bin/env python3
"""Interroge le dictionnaire installé par l'API dont se sert Dictionary.app.

`check.py` porte sur le XML : l'analyse est-elle écrite, et juste ? Celui-ci
porte sur le bundle : la forme se retrouve-t-elle, et une seule fois ? Entre les
deux il y a le compilateur d'Apple et un index trie qu'on ne relit pas à l'œil.

Usage :  python3 scripts/verify_lookup.py [forme…]
"""

import ctypes
import ctypes.util
import pathlib
import plistlib
import sys
import unicodedata

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import build_xml as B  # noqa: E402  — pour retrouver ce qu'on a voulu écrire

ROOT = pathlib.Path(__file__).resolve().parent.parent
BUNDLE = pathlib.Path.home() / "Library/Dictionaries/Conjugaison.dictionary"
DEFAULT_FORMS = ["vis", "fasse", "faites", "visse", "vît", "faire"]

cf = ctypes.CDLL(ctypes.util.find_library("CoreFoundation"))
cs = ctypes.CDLL(ctypes.util.find_library("CoreServices"))

CFIndex = ctypes.c_int64
UTF8 = 0x08000100


class CFRange(ctypes.Structure):
    _fields_ = [("location", CFIndex), ("length", CFIndex)]


for fn, res, args in [
    (cf.CFStringCreateWithCString, ctypes.c_void_p,
     [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint32]),
    (cf.CFStringGetLength, CFIndex, [ctypes.c_void_p]),
    (cf.CFStringGetCString, ctypes.c_bool,
     [ctypes.c_void_p, ctypes.c_char_p, CFIndex, ctypes.c_uint32]),
    (cf.CFSetGetCount, CFIndex, [ctypes.c_void_p]),
    (cf.CFArrayGetCount, CFIndex, [ctypes.c_void_p]),
    (cf.CFArrayGetValueAtIndex, ctypes.c_void_p, [ctypes.c_void_p, CFIndex]),
    (cs.DCSCopyAvailableDictionaries, ctypes.c_void_p, []),
    # Sans restype déclaré, ctypes rend un c_int et tronque le pointeur.
    (cs.DCSGetActiveDictionaries, ctypes.c_void_p, []),
    (cs.DCSDictionaryGetName, ctypes.c_void_p, [ctypes.c_void_p]),
    (cs.DCSDictionaryGetIdentifier, ctypes.c_void_p, [ctypes.c_void_p]),
    (cs.DCSDictionaryGetPrimaryLanguage, ctypes.c_void_p, [ctypes.c_void_p]),
    (cs.DCSCopyRecordsForSearchString, ctypes.c_void_p,
     [ctypes.c_void_p] * 4),
    (cs.DCSRecordGetHeadword, ctypes.c_void_p, [ctypes.c_void_p]),
    (cs.DCSCopyTextDefinition, ctypes.c_void_p,
     [ctypes.c_void_p, ctypes.c_void_p, CFRange]),
]:
    fn.restype, fn.argtypes = res, args
cf.CFSetGetValues.argtypes = [ctypes.c_void_p, ctypes.c_void_p]


def fold(text):
    """Sans diacritiques : le pliage que le DDK applique aux clés supplémentaires."""
    return "".join(c for c in unicodedata.normalize("NFD", text.lower())
                   if not unicodedata.combining(c))


def cfstr(text):
    return cf.CFStringCreateWithCString(None, text.encode("utf-8"), UTF8)


def pystr(ref):
    if not ref:
        return None
    size = (cf.CFStringGetLength(ref) + 1) * 4
    buf = ctypes.create_string_buffer(size)
    if not cf.CFStringGetCString(ref, buf, size, UTF8):
        return None
    return buf.value.decode("utf-8")


def bundle_identifier():
    return plistlib.loads(
        (ROOT / "src" / "Info.plist").read_bytes())["CFBundleIdentifier"]


def find_dictionary(identifier):
    """On demande la référence au système plutôt que de la fabriquer depuis l'URL.

    DCSDictionaryCreate() renvoie NULL même sur un bundle sain — vérifié contre
    websters-1913, qui fonctionne. Le système, lui, tient la liste des
    dictionnaires qu'il a indexés ; en faire partie est déjà la moitié du test.

    On cherche par identifiant, pas par nom : le nom affiché change dès qu'on
    touche à CFBundleDisplayName, et ce vérificateur s'est déjà cassé une fois
    pour cette raison.
    """
    available = cs.DCSCopyAvailableDictionaries()
    count = cf.CFSetGetCount(available) if available else 0
    refs = (ctypes.c_void_p * count)()
    cf.CFSetGetValues(available, refs)
    for ref in refs:
        if pystr(cs.DCSDictionaryGetIdentifier(ref)) == identifier:
            return ref
    return None


def active_identifiers():
    active = cs.DCSGetActiveDictionaries()
    count = cf.CFSetGetCount(active) if active else 0
    refs = (ctypes.c_void_p * count)()
    cf.CFSetGetValues(active, refs)
    return {pystr(cs.DCSDictionaryGetIdentifier(r)) for r in refs}


def main():
    if not BUNDLE.exists():
        sys.exit(f"{BUNDLE} absent. Lancez `make install`.")

    identifier = bundle_identifier()
    dictionary = find_dictionary(identifier)
    if not dictionary:
        sys.exit(
            f"« {identifier} » n'est pas dans la liste du système. Le bundle est "
            "installé mais macOS ne l'a pas indexé : relancez Dictionary.app."
        )

    expected, _, _ = B.build_index(B.load())
    problems = []

    print(f"  {pystr(cs.DCSDictionaryGetName(dictionary))}  [{identifier}]")

    # Actif, sinon rien ne le consultera — ni Dictionary.app, ni la fenêtre ⌃⌘D.
    if identifier not in active_identifiers():
        problems.append(
            "le dictionnaire est installé mais pas coché : Dictionary.app > "
            "Réglages, puis cochez-le")

    # La langue est ce qui décide de sa présence dans la fenêtre de consultation.
    # Dictionary.app ne filtre pas ; ⌃⌘D et le clic maintenu, si.
    language = pystr(cs.DCSDictionaryGetPrimaryLanguage(dictionary))
    print(f"  langue déclarée : {language or 'AUCUNE'}")
    if language != "fr":
        problems.append(
            f"langue « {language} » au lieu de « fr » — la fenêtre de "
            "consultation ne le proposera pas")
    print()
    for form in sys.argv[1:] or DEFAULT_FORMS:
        records = cs.DCSCopyRecordsForSearchString(dictionary, cfstr(form), None, None)
        count = cf.CFArrayGetCount(records) if records else 0
        if not count:
            problems.append(f"« {form} » : aucun enregistrement")
            print(f"  ✗ « {form} »  introuvable")
            continue
        headwords = [pystr(cs.DCSRecordGetHeadword(cf.CFArrayGetValueAtIndex(records, i)))
                     for i in range(count)]

        # Une entrée par forme : la clé doit ramener une seule entrée *exacte*.
        # Les autres sont légitimes à une condition — que ce soit la même forme
        # aux accents près. Le DDK ajoute les clés sans diacritiques, pour que
        # « vecu » trouve « vécu » ; l'effet de bord est que « fit » ramène aussi
        # « fît », ce qui est utile plutôt que faux.
        exact = [h for h in headwords if h == form]
        folded = [h for h in headwords if h != form and fold(h) != fold(form)]
        if len(exact) != 1:
            problems.append(
                f"« {form} » : {len(exact)} entrée exacte sur {count} — {headwords}")
        if folded:
            problems.append(f"« {form} » : entrées étrangères {folded}")

        variants = [h for h in headwords if h != form]
        note = f", plus {', '.join(variants)} par pliage des accents" if variants else ""
        if exact:
            print(f"  ✓ « {form} »  (1 entrée{note})")
        else:
            # Pas une forme du dictionnaire : seulement une graphie sans accents
            # qui y mène. On le dit, plutôt que d'afficher une coche.
            print(f"  ~ « {form} »  pas une forme ; mène à {', '.join(headwords)}")

        # Dictionary.app rend le tableau en texte brut, cellules collées bout à
        # bout. On ne cherche donc pas à le relire — on reconstruit la ligne
        # attendue depuis le générateur et on exige de la retrouver telle quelle.
        text = pystr(cs.DCSCopyTextDefinition(dictionary, cfstr(form),
                                              CFRange(0, len(form)))) or ""
        for record in expected.get(form, []):
            row = (f"{record.verb['infinitif']}{record.conjugated}"
                   f"{B.tense_label(record.slot)}{record.person_label or '—'}")
            mark = "✓" if row in text else "✗"
            if mark == "✗":
                problems.append(f"« {form} » : ligne absente du bundle — {row}")
            print(f"        {mark} {record.verb['infinitif']:<7} "
                  f"{record.conjugated:<16} {B.tense_label(record.slot):<24} "
                  f"{record.person_label or '—'}")

    if problems:
        print()
        for problem in problems:
            print(f"  ✗ {problem}")
        sys.exit(1)
    print("  le bundle répond")


if __name__ == "__main__":
    main()
