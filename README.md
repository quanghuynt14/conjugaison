# Conjugaison — un dictionnaire macOS des formes conjuguées

Preuve de concept. Vous sélectionnez `fasse` dans n'importe quelle application,
vous faites ⌃⌘D, et vous obtenez la conjugaison complète de *faire*, arrêtée sur
le subjonctif présent.

Deux verbes pour l'instant : **faire** et **avoir**. 85 formes indexées.

## Essayer

Le dictionnaire est déjà compilé et installé. Il reste à le cocher :

1. Ouvrez **Dictionary.app**.
2. Menu **Dictionnaire › Réglages** (ou ⌘,).
3. Cochez **Conjugaison** dans la liste, et montez-le si vous le voulez en tête.
4. Cherchez `fasse`.

Puis, hors de Dictionary.app : sélectionnez `fissiez` dans un texte et faites ⌃⌘D.

Pour vérifier sans ouvrir quoi que ce soit :

```bash
make verify        # interroge le bundle installé par l'API de macOS
```

## Ce que ça fait

Une entrée par **verbe**, indexée par toutes ses **formes**. Chercher `fasse`
ouvre l'entrée `faire` ; la liste des résultats affiche `fasse (faire)`, ce qui
lève l'ambiguïté quand plusieurs verbes partagent une forme — et le français en
partage beaucoup (`vis` est à la fois *vivre*, *voir* et *visser*).

Chaque forme porte une **ancre** vers son temps, donc l'entrée s'ouvre sur la
bonne case et pas en haut du tableau. C'est le mécanisme des dictionnaires
d'Apple eux-mêmes, où `made` renvoie à `make`.

Les temps composés ne sont pas stockés. Ils sont **construits** à partir de
l'auxiliaire conjugué et du participe passé, parce que c'est ce qu'un temps
composé *est*. Écrire « j'ai fait » dans les données serait écrire un fait que la
grammaire donne déjà. C'est aussi pourquoi `avoir` est dans le jeu de données :
sans lui, `faire` n'a pas de passé composé.

Les composés ne sont pas indexés non plus. « ai fait » fait deux mots : ce n'est
pas une recherche, et `d:value` n'accepte pas l'espace.

## Ce qui existe déjà, et qu'il faut savoir avant d'aller plus loin

macOS livre deux dictionnaires qui résolvent déjà les formes fléchies du
français : **Oxford-Hachette** et le **Multidictionnaire de la langue
française**. `make verify` le montre — cherchez `fissiez`, les trois répondent.

Le Multidictionnaire est excellent, mais il répond en **lexicographe** : il ouvre
sur la prononciation, les sens, les emplois. Le tableau de conjugaison n'est pas
ce qu'il vous met sous les yeux. Celui-ci ne fait que ça, et le met en premier.

C'est une différence réelle, mais mince. Elle mérite d'être pesée avant
d'encoder six mille verbes.

## Construire

```bash
make            # setup + xml + compilation + installation
make check      # la forme est-elle dans le XML ?
make verify     # le bundle installé sait-il y répondre ?
make uninstall
```

`make setup` clone le **Dictionary Development Kit** d'Apple dans `tools/`. Il
n'est pas commité : il appartient à Apple. Ses binaires sont **x86_64
uniquement**, donc sur Apple Silicon il faut Rosetta 2 :

```bash
softwareupdate --install-rosetta --agree-to-license
```

`build_dict.sh` vise macOS 10.5 par défaut et écrit alors les données dans
`Contents/` — une disposition que les macOS récents ne lisent plus. Le Makefile
passe `-v 10.11`, qui produit `Contents/Resources/`, un index trie et
`IDXDictionaryVersion 3`. C'est la disposition des dictionnaires d'Apple.

## Disposition

- `data/verbs.json` — les verbes. Six formes par temps, dans l'ordre
  je / tu / il / nous / vous / ils ; trois pour l'impératif.
- `scripts/build_xml.py` — le générateur. Il tient l'ordre des temps, l'élision
  (`que` + `il` → `qu'il`) et la construction des composés.
- `scripts/check.py` — relit le XML produit. Il cherche la panne qui ne se voit
  pas : la forme **absente**. Rien ne la référence, rien ne s'en plaint, et elle
  ne se manifeste que le jour où on la cherche et où il ne se passe rien.
- `scripts/verify_lookup.py` — interroge le bundle **installé** via
  DictionaryServices, l'API dont se sert Dictionary.app. Entre le XML et le
  bundle il y a le compilateur d'Apple et un index qu'on ne relit pas à l'œil ;
  c'est le seul contrôle qui traverse tout.
- `src/conjugaison.css` — deux voix typographiques, comme dans *rappel* : le
  français conjugué en romain à empattements, les étiquettes en sans. Les
  accents sur du petit texte sont précisément ce qu'on lit ici.
- `src/Info.plist` — identité du bundle. Le reste du plist est engendré par le
  DDK.

## Après la preuve de concept

Le générateur est déjà écrit pour l'échelle ; ce sont les **données** qui
manquent. Il faudrait :

- une source de conjugaisons libre de droits — Morphalou (CNRTL, licence LGPL-LR)
  ou le Lexique 3 donnent les formes fléchies du français par dizaines de
  milliers ;
- décider quoi faire des homographes entre verbes. Une forme n'a qu'une entrée
  par verbe, mais `vis` doit produire trois lignes dans la liste des résultats ;
- les verbes pronominaux et l'accord du participe passé avec `être`, qui ne se
  déduit pas de l'auxiliaire seul.

Rien de tout ça ne change l'architecture. Un verbe de plus est un objet de plus
dans `verbs.json`.
