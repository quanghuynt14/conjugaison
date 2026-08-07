#!/usr/bin/env python3
"""Interroge le dictionnaire compilé par l'API que Dictionary.app utilise elle-même.

Le contrôle de `check.py` porte sur le XML : la forme est-elle écrite ? Celui-ci
porte sur le bundle : la forme se retrouve-t-elle ? Entre les deux il y a le
compilateur d'Apple, un index trie qu'on ne relit pas à l'œil, et la seule façon
honnête de savoir est de poser la question à DictionaryServices.

Usage :  python3 scripts/verify_lookup.py [forme…]
"""

import ctypes
import ctypes.util
import pathlib
import sys

BUNDLE = pathlib.Path.home() / "Library/Dictionaries/Conjugaison.dictionary"
DEFAULT_FORMS = ["fasse", "fît", "faites", "ferions", "eussent", "faire"]

cf = ctypes.CDLL(ctypes.util.find_library("CoreFoundation"))
cs = ctypes.CDLL(ctypes.util.find_library("CoreServices"))

CFIndex = ctypes.c_int64
kCFStringEncodingUTF8 = 0x08000100


class CFRange(ctypes.Structure):
    _fields_ = [("location", CFIndex), ("length", CFIndex)]


cf.CFStringCreateWithCString.restype = ctypes.c_void_p
cf.CFStringCreateWithCString.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint32]
cf.CFURLCreateWithFileSystemPath.restype = ctypes.c_void_p
cf.CFURLCreateWithFileSystemPath.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                             ctypes.c_uint32, ctypes.c_bool]
cf.CFArrayGetCount.restype = CFIndex
cf.CFArrayGetCount.argtypes = [ctypes.c_void_p]
cf.CFArrayGetValueAtIndex.restype = ctypes.c_void_p
cf.CFArrayGetValueAtIndex.argtypes = [ctypes.c_void_p, CFIndex]
cf.CFStringGetLength.restype = CFIndex
cf.CFStringGetLength.argtypes = [ctypes.c_void_p]
cf.CFStringGetCString.restype = ctypes.c_bool
cf.CFStringGetCString.argtypes = [ctypes.c_void_p, ctypes.c_char_p, CFIndex, ctypes.c_uint32]

cf.CFSetGetCount.restype = CFIndex
cf.CFSetGetCount.argtypes = [ctypes.c_void_p]
cf.CFSetGetValues.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

cs.DCSCopyAvailableDictionaries.restype = ctypes.c_void_p
cs.DCSDictionaryGetName.restype = ctypes.c_void_p
cs.DCSDictionaryGetName.argtypes = [ctypes.c_void_p]
cs.DCSCopyRecordsForSearchString.restype = ctypes.c_void_p
cs.DCSCopyRecordsForSearchString.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                             ctypes.c_void_p, ctypes.c_void_p]
cs.DCSRecordGetHeadword.restype = ctypes.c_void_p
cs.DCSRecordGetHeadword.argtypes = [ctypes.c_void_p]
cs.DCSRecordGetAnchor.restype = ctypes.c_void_p
cs.DCSRecordGetAnchor.argtypes = [ctypes.c_void_p]
cs.DCSCopyTextDefinition.restype = ctypes.c_void_p
cs.DCSCopyTextDefinition.argtypes = [ctypes.c_void_p, ctypes.c_void_p, CFRange]


def cfstr(text):
    return cf.CFStringCreateWithCString(None, text.encode("utf-8"), kCFStringEncodingUTF8)


def pystr(ref):
    if not ref:
        return None
    size = (cf.CFStringGetLength(ref) + 1) * 4
    buf = ctypes.create_string_buffer(size)
    if not cf.CFStringGetCString(ref, buf, size, kCFStringEncodingUTF8):
        return None
    return buf.value.decode("utf-8")


def find_dictionary(name):
    """On demande la référence au système plutôt que de la fabriquer depuis l'URL.

    DCSDictionaryCreate() renvoie NULL même sur un bundle sain — vérifié contre
    websters-1913, qui fonctionne. Le système, lui, tient une liste des
    dictionnaires qu'il a indexés ; en faire partie est déjà la moitié du test.
    """
    available = cs.DCSCopyAvailableDictionaries()
    count = cf.CFSetGetCount(available) if available else 0
    refs = (ctypes.c_void_p * count)()
    cf.CFSetGetValues(available, refs)
    for ref in refs:
        if pystr(cs.DCSDictionaryGetName(ref)) == name:
            return ref
    return None


def main():
    if not BUNDLE.exists():
        sys.exit(f"{BUNDLE} absent. Lancez `make install`.")

    dictionary = find_dictionary(BUNDLE.stem)
    if not dictionary:
        sys.exit(
            f"« {BUNDLE.stem} » n'est pas dans la liste du système. Le bundle est "
            "installé mais macOS ne l'a pas indexé : relancez Dictionary.app."
        )

    forms = sys.argv[1:] or DEFAULT_FORMS
    missing = []

    for form in forms:
        records = cs.DCSCopyRecordsForSearchString(dictionary, cfstr(form), None, None)
        count = cf.CFArrayGetCount(records) if records else 0
        if not count:
            missing.append(form)
            print(f"  ✗ « {form} » : aucun enregistrement")
            continue
        for i in range(count):
            record = cf.CFArrayGetValueAtIndex(records, i)
            headword = pystr(cs.DCSRecordGetHeadword(record))
            anchor = pystr(cs.DCSRecordGetAnchor(record)) or "—"
            print(f"  ✓ « {form} » → {headword}   ancre {anchor}")

    # Ce que fera ⌃⌘D : cherche dans les dictionnaires *activés*. Un échec ici
    # ne veut pas dire que le bundle est cassé, seulement qu'il reste à cocher.
    probe = "fasse"
    text = pystr(cs.DCSCopyTextDefinition(None, cfstr(probe), CFRange(0, len(probe))))
    print()
    if text:
        print(f"Recherche système sur « {probe} » : {text.splitlines()[0][:70]}…")
    else:
        print(f"Recherche système sur « {probe} » : rien — le dictionnaire n'est "
              "pas encore coché dans les réglages de Dictionary.app.")

    if missing:
        sys.exit(f"\nFormes introuvables : {', '.join(missing)}")


if __name__ == "__main__":
    main()
