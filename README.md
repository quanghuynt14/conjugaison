# Conjugaison — une conjugaison inversée pour macOS

Preuve de concept. Vous sélectionnez `vis` dans n'importe quelle application,
vous faites ⌃⌘D, et la page s'ouvre sur ceci :

***vivre***

| conjugaison | temps |
|---|---|
| je vis | Indicatif présent |
| tu vis | Indicatif présent |
| vis | Impératif présent |

***voir***

| conjugaison | temps |
|---|---|
| je vis | Indicatif passé simple |
| tu vis | Indicatif passé simple |

Puis la conjugaison complète de *vivre* et de *voir*, les cases d'où vient la
forme surlignées.

Quatre verbes : **faire**, **avoir**, **vivre**, **voir**. 162 formes,
564 analyses.

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
liste toutes.

### Un tableau par verbe

`vis` est de vivre et de voir. Ce sont deux réponses, pas cinq lignes d'une
même liste, et la page le dit maintenant en deux tableaux — chacun avec le verbe
en légende.

Le verbe quitte donc les colonnes. Il y répétait le même mot à chaque ligne, et
pour `vécu` il l'aurait répété quarante-six fois sans jamais rien apprendre.
En légende, il le dit une fois et sert de titre. Restent deux colonnes : ce qui
change d'une ligne à l'autre.

L'ordre en découle. **Verbe alphabétique** — c'est le découpage en tableaux —
puis, dans chaque tableau, **temps selon `PLAN`** : mode, puis temps dans le
mode. Indicatif présent, Indicatif passé composé, Indicatif imparfait… le même
ordre que les conjugaisons du bas de la page. Cet ordre est une convention
déclarée, pas un modèle de fréquence — c'est ce qui permet à `check.py` de
l'affirmer.

#### Deux tableaux ne se voient pas

Et c'est le défaut qu'on n'avait pas vu venir. En calage automatique, chaque
tableau répartit sa largeur selon son seul contenu : `Indicatif passé simple`
étant plus long que `Indicatif présent`, le tableau de *voir* décalait sa
colonne des temps par rapport à celui de *vivre*. Empilées, les deux grilles ne
tombaient pas au même endroit, et la page avait l'air cassée.

D'où `table-layout: fixed` et une première colonne à **44 %** — le rapport des
contenus les plus longs, `que vous eussiez vécu` contre
`Subjonctif plus-que-parfait`. En pourcentage, pas en `em` : la grille suit la
fenêtre au lieu de lui imposer une largeur.

Une colonne de largeur fixe déborde si rien ne peut se replier. La conjugaison
se replie donc, mais **entre les mots seulement** — `que nous ayons` puis `vécu`
à la ligne, jamais une coupure au milieu de `eussiez`. Une forme coupée en deux
ne se lit plus comme une forme.

Mesuré à 320 px sur l'entrée la plus large, `vécu` : aucun débordement, et les
deux colonnes `TEMPS` de `vis` commencent au même pixel.

### La colonne « personne » a été corrigée, puis supprimée

Elle disait `1ʳᵉ du singulier` en face de `je vis`, et `masculin singulier` en
face de `vécu`. La seconde moitié était fausse — un participe n'a pas de
personne, il s'accorde en genre et en nombre. On l'a donc rebaptisée **accord**,
qui couvre les deux : un verbe s'accorde avec son sujet en personne et en
nombre, un participe en genre et en nombre.

Puis on a mesuré ce qu'elle apprenait. **504 lignes sur 564 répétaient le pronom
déjà visible** : `je vis` suivi de `1ʳᵉ du singulier`. Et aucune paire
(conjugaison, temps) ne se répète dans un tableau — l'accord était donc une
fonction des deux autres colonnes, incapable de distinguer une ligne d'une
autre. Il ne distinguait pas, il nommait.

Restaient 52 lignes sans pronom : l'impératif et le participe. Elles ne
sauvent pas la colonne. Les trois impératifs d'un verbe sont toujours distincts
— `fais / faisons / faites` — et le `-ons`, le `-ez` portent la personne. Les
quatre participes le sont aussi, et le `-e`, le `-s` portent le genre et le
nombre ; la conjugaison du bas surligne déjà lequel des quatre. Rien de ce qui
**identifie** la forme ne disparaît avec la colonne.

Ce qui disparaît, c'est le nom de la catégorie : savoir que le `-ez` de `vivez`
s'appelle « 2ᵉ du pluriel ». Trente-six lignes le méritaient. Cinq cent quatre
paraphrasaient. Une définition doit apprendre quelque chose — c'est la barre de
[l'article de Somers](https://jsomers.net/blog/dictionary), et à 89 % de
répétition la colonne ne la tenait pas.

`check.py` garde l'invariant qui rend la suppression sûre : deux lignes
identiques dans un tableau sont une erreur. Le jour où une paire se répète,
l'accord manquera vraiment.

`Participe passé` dans la colonne des temps, en revanche, était juste et le
reste. Le participe est un mode impersonnel, au même titre que l'indicatif est
un mode personnel, et le passé est un de ses deux temps. La cellule a la même
forme que `Indicatif présent` : mode puis temps. La seule qui s'arrêtait au mode
était `Infinitif`, seule sur dix-neuf ; elle dit maintenant `Infinitif présent`.

Les temps composés sont **construits**, pas stockés : l'auxiliaire conjugué plus
le participe passé, parce que c'est ce qu'un temps composé est. D'où `avoir`
dans les données — sans lui, `faire` n'a pas de passé composé. Ils ne sont pas
indexés : « ai fait » fait deux mots, et `d:value` n'accepte pas l'espace.

### Le tableau dit aussi où la forme apparaît

Une case composée cite deux formes cherchables. « j'ai vécu » en cite deux :
`ai` et `vécu`. Chacune reçoit sa ligne dans le tableau de l'autre.

Sans ça, chercher `vécu` répondait « participe passé » et s'arrêtait là. Vrai,
et muet sur les quarante-cinq cases où la forme travaille — alors que celui qui
sélectionne `vécu` l'a presque toujours lu dans « j'ai vécu ». Son tableau fait
maintenant 46 lignes.

`ai` est la trouvaille. Il ouvre **quatre** tableaux : avoir, où il est le
présent puis l'auxiliaire du passé composé, et faire, vivre, voir, où il n'est
que l'auxiliaire. Le dictionnaire ne disait nulle part qu'`ai` est un auxiliaire.

Ces lignes ne sont pas groupées à part : elles prennent leur rang dans l'ordre
des temps, comme les autres. Pour `vécu`, `Participe passé` arrive donc en
dernier — c'est le dernier temps de `PLAN` — après les quarante-cinq composés
qui le citent. Un tableau qui suit une seule règle, au prix de la réponse la
plus directe qui n'est plus en tête.

Ce qui la rend repérable, c'est la graisse. Une ligne qui dit ce que la forme
**est** garde sa conjugaison en gras ; une ligne qui dit où elle **apparaît** la
perd. Sur quarante-six lignes, l'œil trouve la bonne sans lire la colonne des
temps. `check.py` exige par ailleurs qu'aucune entrée ne soit faite que de lignes
citées : une clé est d'abord une forme.

Le nombre de clés, lui, ne bouge pas — 162 avant, 162 après. Une case composée
ne cite que des formes déjà indexées. On ajoute des lignes, jamais des entrées,
et « ai fait » reste introuvable en tant que tel.

### Les accents se plient, et c'est voulu

Le DDK ajoute pour chaque clé accentuée une clé sans diacritiques. `vecu` trouve
`vécu`, `fimes` trouve `fîmes`. Pour une application dont le public est
précisément celui qui hésite sur les accents, c'est l'inverse d'un défaut.

L'effet de bord : `fit` ramène deux entrées, `fit` et `fît`. Le passé simple et
le subjonctif imparfait de *faire*, côte à côte. Utile. Même chose pour `eut` /
`eût` et `vit` / `vît`. `verify_lookup.py` l'autorise explicitement : une seule
entrée **exacte**, et les autres doivent être la même forme aux accents près.

## Réinstaller par-dessus casse la fenêtre de consultation

C'est la panne qui a coûté le plus cher, et elle n'est dans aucun fichier du
projet : elle est dans la façon d'installer.

`ditto` par-dessus un bundle déjà en place laisse macOS avec un index périmé. Le
dictionnaire continue de répondre à l'API — `make verify` passait, les 162
formes revenaient justes — et **disparaît de la fenêtre de consultation**.
Dictionary.app, lui, continue de marcher. D'où le diagnostic impossible : tout
ce qu'un script peut interroger dit que tout va bien.

`make install` fait donc `rm -rf` sur la destination avant de copier, puis
appelle `make refresh`.

### `killall LookupViewService` ne relance rien

Et c'est la moitié de l'histoire. Ce sont des services **XPC** : `killall` ne les
reconnaît pas et sort sans rien dire. Il en tourne **un par application hôte**,
chacun garde la liste des dictionnaires pour toute sa durée de vie — on en a
trouvé deux vieux de la veille, lancés avant que le projet existe.

D'où l'impression, pendant toute une séance, qu'aucune correction n'avait
d'effet : la fenêtre répondait depuis un état antérieur à tout ce qu'on faisait.

```make
refresh:
	@pkill -9 -f LookupViewService
	@pkill -9 -f DictionaryServiceHelper
	@killall cfprefsd
```

`pkill -f` vise la ligne de commande complète, et lui les atteint.

### Comment on l'a su

Trois hypothèses successives — identifiant, langue déclarée, index de référence
vide — chacune plausible, chacune corrigée, aucune n'ayant rien changé. La
sortie a été d'installer **cinq variantes côte à côte**, isolant un facteur
chacune, et de faire un seul clic maintenu :

| | identifiant | langue | index de référence |
|---|---|---|---|
| A | `fr.huy.*` | `fr` | peuplé |
| B | `fr.huy.*` | aucune | peuplé |
| C | `fr.huy.*` | `fr` | vide |
| D | `com.apple.*` | aucune | peuplé |
| E | `fr.huy.*` | aucune | vide |

**Les cinq sont apparues.** Aucun des trois facteurs ne conditionnait la
visibilité ; installées proprement, toutes marchaient. Ce qui distinguait le
dictionnaire cassé n'était pas son contenu mais son installation.

Une variante isole un facteur ; cinq installées ensemble isolent tout l'espace
en un essai. À refaire dès qu'une panne ne se voit que dans une fenêtre.

### Ce que l'ordre a appris

Elles sont sorties dans l'ordre D, B, E, C, A : les trois **sans langue
déclarée** d'abord, les deux qui déclaraient `fr` ensuite. Déclarer la langue ne
conditionne pas la visibilité — elle **dégrade le classement**. Les clés ont donc
été retirées, et `make verify` refuse maintenant qu'on en déclare une.
websters-1913 n'en déclare aucune non plus.

## L'index de référence, gardé sans être la cause

Le DDK ne met dans `EntryID.index` que les entrées *citées* — par un lien
`x-dictionary:r:` ou par `DCSDictionaryFrontMatterReferenceID`. Sans l'un ni
l'autre l'index sort vide, et le build le dit à chaque fois avant de continuer :

```
- Building reference index.
* Note: No reference index record.
```

L'interrupteur n'est documenté que dans le code de `build_dict.sh` :

```make
preserve_unused_ref_id_in_reference_index=1 "$(DDK_BIN)/build_dict.sh" …
```

`EntryID.data` passe de 64 octets à 22 592. C'est gardé, et le Makefile fait de
l'avertissement une erreur — un index de référence vide reste un défaut, et
websters-1913 a le sien peuplé. Mais **ce n'était pas la cause** de la fenêtre
vide : la variante E, index vide, s'affichait très bien.

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
