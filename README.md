# Conjugaison — une conjugaison inversée pour macOS

Preuve de concept. Vous sélectionnez `vis` dans n'importe quelle application,
vous faites ⌃⌘D, et la page s'ouvre sur ceci :

| verbe | conjugaison | temps | personne |
|---|---|---|---|
| vivre | je vis | Indicatif présent | 1ʳᵉ du singulier |
| vivre | tu vis | Indicatif présent | 2ᵉ du singulier |
| vivre | vis | Impératif présent | 2ᵉ du singulier |
| voir | je vis | Indicatif passé simple | 1ʳᵉ du singulier |
| voir | tu vis | Indicatif passé simple | 2ᵉ du singulier |

Puis la conjugaison complète de *vivre* et de *voir*, les cases d'où vient la
forme surlignées.

Quatre verbes : **faire**, **avoir**, **vivre**, **voir**. 162 formes,
204 analyses.

## Essayer

Le dictionnaire est compilé et installé. Il reste à le cocher :

1. Ouvrez **Dictionary.app**.
2. **Dictionnaire › Réglages** (⌘,).
3. Cochez **Conjugaison**, et montez-le en tête si vous voulez.
4. Cherchez `vis`, puis `fasse`, puis `faites`.

Sans ouvrir l'app :

```bash
make verify        # interroge le bundle installé par l'API de macOS
```

## Le découpage : une entrée par forme

C'est la décision qui tient tout le reste.

Dictionary.app rend **un corps par entrée**. Une entrée par verbe rendrait donc
le même corps pour ses quarante clés : le haut de la page ne peut pas savoir
quelle forme vous avez tapée, et une conjugaison inversée n'est que ça. Une
entrée par forme le sait.

Une forme peut avoir plusieurs analyses **dans un même verbe et un même mode** :
`dis` est le présent *et* le passé simple de dire. On ne choisit jamais, on les
liste toutes, dans l'ordre : verbe alphabétique, puis temps dans l'ordre de
`PLAN`, puis personne. Cet ordre est une convention déclarée, pas un modèle de
fréquence — c'est ce qui permet à `check.py` de l'affirmer.

Les temps composés sont **construits**, pas stockés : l'auxiliaire conjugué plus
le participe passé, parce que c'est ce qu'un temps composé est. D'où `avoir`
dans les données — sans lui, `faire` n'a pas de passé composé. Ils ne sont pas
indexés : « ai fait » fait deux mots, et `d:value` n'accepte pas l'espace.

### Les accents se plient, et c'est voulu

Le DDK ajoute pour chaque clé accentuée une clé sans diacritiques. `vecu` trouve
`vécu`, `fimes` trouve `fîmes`. Pour une application dont le public est
précisément celui qui hésite sur les accents, c'est l'inverse d'un défaut.

L'effet de bord : `fit` ramène deux entrées, `fit` et `fît`. Le passé simple et
le subjonctif imparfait de *faire*, côte à côte. Utile. Même chose pour `eut` /
`eût` et `vit` / `vît`. `verify_lookup.py` l'autorise explicitement : une seule
entrée **exacte**, et les autres doivent être la même forme aux accents près.

## La fenêtre de consultation filtre par langue

Un dictionnaire peut très bien marcher dans Dictionary.app et rester invisible
au clic maintenu et à ⌃⌘D. C'est arrivé ici, et ce n'est pas un défaut du
bundle : **Dictionary.app ne filtre pas par langue, la fenêtre de consultation
si**. Sans langue déclarée, elle ne propose jamais le dictionnaire.

Les trois clés qui manquaient, telles que les déclarent les dictionnaires
français livrés par macOS :

```xml
<key>DCSDictionaryPrimaryLanguage</key><string>fr</string>
<key>DCSDictionaryLanguages</key>
<array><dict>
  <key>DCSDictionaryDescriptionLanguage</key><string>fr</string>
  <key>DCSDictionaryIndexLanguage</key><string>fr</string>
</dict></array>
<key>DCSDictionaryUseSystemAppearance</key><true/>
```

La dernière n'a rien à voir avec la recherche : sans elle la fenêtre reste
blanche en thème sombre, et le `prefers-color-scheme` du CSS ne sert à rien.

Le DDK laisse passer les clés qu'il ne connaît pas, y compris les tableaux
imbriqués — vérifié sur le plist compilé. `make verify` affiche désormais la
langue déclarée et refuse de passer si ce n'est pas `fr`, parce que c'est une
panne qui ne se voit que dans une fenêtre qu'aucun script n'ouvre.

Après un changement de plist, il faut relancer les services qui gardent ces
métadonnées en cache :

```bash
killall LookupViewService Dictionary DictionaryServiceHelper
```

## Ce qui existe déjà, et qu'il faut savoir

macOS livre **Oxford-Hachette** et le **Multidictionnaire de la langue
française**, qui résolvent déjà les formes fléchies. Cherchez `fissiez` : les
trois répondent.

Le Multidictionnaire est excellent, mais il répond en lexicographe — la
prononciation, les sens, les emplois. Il ne vous dit pas *quelle personne de
quel temps* vous avez sous les yeux. C'est le seul trou que celui-ci remplit,
et il vaut la peine d'être pesé avant d'encoder six mille verbes.

## Construire

```bash
make            # setup + xml + compilation + installation
make check      # l'analyse est-elle écrite, et juste ?
make verify     # le bundle installé sait-il y répondre ?
make uninstall
```

Les deux contrôles ne se recouvrent pas. `check.py` relit le XML ; `verify_lookup.py`
interroge le bundle installé. Entre les deux il y a le compilateur d'Apple et un
index trie qu'on ne relit pas à l'œil, donc seul le second traverse tout. Il sait
aussi balayer le dictionnaire entier :

```bash
python3 scripts/verify_lookup.py $(python3 -c "
import sys; sys.path.insert(0,'scripts'); import build_xml as B
print(' '.join(sorted(B.build_index(B.load())[0])))")
```

`make setup` clone le **Dictionary Development Kit** d'Apple dans `tools/`. Il
n'est pas commité : il appartient à Apple. Ses binaires sont **x86_64
uniquement**, donc sur Apple Silicon il faut Rosetta 2 :

```bash
softwareupdate --install-rosetta --agree-to-license
```

`build_dict.sh` vise macOS 10.5 par défaut et écrit les données dans
`Contents/`, une disposition que les macOS récents ne lisent plus. Le Makefile
passe `-v 10.11`, qui produit `Contents/Resources/`, un index trie et
`IDXDictionaryVersion 3` — la disposition des dictionnaires d'Apple.

## Ce que ça coûte à l'échelle

Mesuré sur 501 verbes synthétiques, les deux découpages compilés :

| | par verbe | par forme |
|---|---|---|
| entrées | 276 | 11 869 |
| XML source | 3,1 Mo | 79 Mo |
| **bundle** | **2,88 Mo** | **2,82 Mo** |
| compilation | rapide | 80 s |

Le disque ne bouge pas : les tableaux quasi identiques se compressent entre eux,
et l'index rétrécit autant que le corps grossit. À 6 000 verbes, comptez ~34 Mo
et **une quinzaine de minutes de compilation**. C'est le seul vrai coût.

## Disposition

- `data/verbs.json` — les verbes. Six formes par temps, dans l'ordre
  je / tu / il / nous / vous / ils ; trois pour l'impératif.
- `scripts/build_xml.py` — le générateur. `analyses_of()` produit les analyses
  d'un verbe, `build_index()` les fusionne par forme, `render_entry()` écrit
  l'entrée. `build_index()` est isolé pour que le vérificateur puisse comparer le
  bundle à ce qu'on a voulu écrire.
- `scripts/check.py` — relit le XML. Il cherche la panne qui ne se voit pas : la
  forme **absente** et l'analyse **fausse**. Il vérifie aussi qu'une clé
  n'apparaît qu'une fois — deux, et la liste de résultats double une recherche.
- `scripts/verify_lookup.py` — interroge le bundle **installé** via
  DictionaryServices, l'API de Dictionary.app.
- `src/conjugaison.css` — deux voix typographiques : le français conjugué en
  romain à empattements, les étiquettes en sans. Les accents sur du petit texte
  sont ce qu'on lit ici.
- `src/Info.plist` — l'identité du bundle. Le DDK engendre le reste.

## Après la preuve de concept

Le générateur est écrit pour l'échelle ; ce sont les **données** qui manquent.

- **Une source libre.** Wiktionnaire est en CC-BY-SA et stocke déjà la bonne
  forme — « Première personne du singulier du passé simple de voir » est une
  analyse inversée en prose. Pour du volume, **Morphalou** (CNRTL, LGPL-LR) ou
  **Lexique 3** donnent la même chose en tables étiquetées.
- **leconjugueur n'est pas une source.** C'est celui du Figaro, et il est
  protégé. Il peut arbitrer une réponse qu'on lui soumet ; il ne peut pas
  fournir de contenu. Même règle que les volumes CLE dans *rappel*.
- **Les pronominaux et l'accord avec `être`**, qui ne se déduit pas de
  l'auxiliaire seul.

Rien de tout ça ne change l'architecture. Un verbe de plus est un objet de plus
dans `verbs.json`.
