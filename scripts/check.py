#!/usr/bin/env python3
"""Contrôle du XML généré, avant de le donner au compilateur d'Apple.

La panne qu'on cherche n'est pas un XML malformé — xmllint la voit, et le build
s'arrête. C'est la forme *absente* : rien ne la référence, rien ne s'en plaint,
et elle ne se manifeste que le jour où on la cherche dans Dictionary.app et où
il ne se passe rien. Donc on compte, et on vérifie que chaque ancre pointe
quelque part.

Usage :  python3 scripts/check.py [forme…]
"""

import pathlib
import re
import sys
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
XML = ROOT / "src" / "conjugaison.xml"
D = "{http://www.apple.com/DTDs/DictionaryService-1.0.rng}"
XPOINTER = re.compile(r"xpointer\(//\*\[@id='([^']+)'\]\)")


def main():
    if not XML.exists():
        sys.exit(f"{XML} absent. Lancez d'abord `make xml`.")

    tree = ET.parse(XML)
    entries = tree.getroot().findall(f"{D}entry")

    index = {}       # forme -> [(titre, ancre, verbe)]
    problems = []

    for entry in entries:
        title = entry.get(f"{D}title")
        ids = {el.get("id") for el in entry.iter() if el.get("id")}

        for node in entry.findall(f"{D}index"):
            value = node.get(f"{D}value")
            if not value:
                problems.append(f"{title} : un <d:index> sans d:value")
                continue
            if " " in value:
                problems.append(f"{title} : d:value « {value} » contient une espace")

            anchor = node.get(f"{D}anchor")
            if anchor:
                match = XPOINTER.match(anchor)
                if not match:
                    problems.append(f"{title} / {value} : ancre illisible « {anchor} »")
                elif match.group(1) not in ids:
                    problems.append(
                        f"{title} / {value} : ancre vers « {match.group(1) }», "
                        "qui n'existe pas dans l'entrée"
                    )
            index.setdefault(value, []).append((node.get(f"{D}title"), anchor, title))

    print(f"{len(entries)} entrées, {len(index)} formes distinctes indexées")
    for entry in entries:
        title = entry.get(f"{D}title")
        count = len(entry.findall(f"{D}index"))
        print(f"  {title:<12} {count:>4} formes")

    for form in sys.argv[1:]:
        hits = index.get(form)
        if not hits:
            problems.append(f"« {form} » n'est dans aucun index — introuvable dans Dictionary.app")
            continue
        for label, anchor, verb in hits:
            where = XPOINTER.match(anchor).group(1) if anchor else "(entrée)"
            print(f"  « {form} » → {verb}, affiché « {label} », ancre {where}")

    if problems:
        print()
        for problem in problems:
            print(f"  ✗ {problem}")
        sys.exit(1)


if __name__ == "__main__":
    main()
