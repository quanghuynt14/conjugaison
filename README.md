# Conjugaison — une conjugaison inversée pour macOS

Vous sélectionnez `vis` dans n'importe quelle application, vous faites ⌃⌘D, et
la page s'ouvre sur ceci :

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

**1 004 verbes** : les mille plus fréquents du français, plus les quatre écrits
à la main avant que l'import existe. 38 917 formes, 96 435 analyses.

## Essayer

Le dictionnaire est compilé et installé. Il reste à le cocher :

1. Ouvrez **Dictionary.app**.
2. **Dictionnaire › Réglages** (⌘,).
3. Cochez **Conjugaison**, et montez-le en tête si vous voulez.
4. Cherchez `vis`, puis `fasse`, puis `faites`. Puis `souviens`, `faut`,
   `paye`, `pris`.

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

`ai` était la trouvaille. À quatre verbes, il ouvrait **quatre** tableaux :
avoir, où il est le présent puis l'auxiliaire du passé composé, et faire,
vivre, voir, où il n'est que l'auxiliaire. Le dictionnaire ne disait nulle part
qu'`ai` est un auxiliaire.

À mille verbes, il en ouvre **neuf cent cinquante-six** — sept mégaoctets, la
même ligne recopiée. Voir plus bas ce qu'on en a fait.

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

Le nombre de clés, lui, ne bouge pas — 162 avant, 162 après, sur les quatre
verbes d'alors. Une case composée ne cite que des formes déjà indexées. On
ajoute des lignes, jamais des entrées, et « ai fait » reste introuvable en tant
que tel.

### Les accents se plient, et c'est voulu

Le DDK ajoute pour chaque clé accentuée une clé sans diacritiques. `vecu` trouve
`vécu`, `fimes` trouve `fîmes`. Pour une application dont le public est
précisément celui qui hésite sur les accents, c'est l'inverse d'un défaut.

L'effet de bord : `fit` ramène deux entrées, `fit` et `fît`. Le passé simple et
le subjonctif imparfait de *faire*, côte à côte. Utile. Même chose pour `eut` /
`eût` et `vit` / `vît`. `verify_lookup.py` l'autorise explicitement : une seule
entrée **exacte**, et les autres doivent être la même forme aux accents près.

## Mille verbes, et d'où ils viennent

Quatre verbes s'écrivent à la main. Mille, non : ce sont mille occasions de se
tromper d'un accent circonflexe. Ils viennent de deux sources citables, et
`scripts/import_verbs.py` n'invente rien entre les deux.

**Verbiste** (Pierre Sarrazin, GPL) donne les formes : 146 modèles de
terminaisons, et chaque verbe rattaché au sien. `parler` plus le modèle `aim:er`
donne `je parle`. C'est la méthode d'un Bescherelle — un tableau, un renvoi. On
le prend chez [verbecc](https://github.com/bretttolbert/verbecc), qui
l'entretient.

**Lexique 3.83** (New & Pallier) donne l'ordre, et « les mille plus fréquents »
veut dire quelque chose de précis : la moyenne des fréquences par lemme dans les
sous-titres de films et dans les livres, par million de mots. Le classement est
versionné dans `data/frequence.txt` — mille imports n'ont pas à relire
vingt-cinq mégaoctets chacun.

Le premier essai a porté sur les quatre verbes déjà écrits : l'import devait les
retrouver **case pour case**. Zéro écart. C'est ce qui a autorisé les mille
suivants, et `import_verbs.py --verifie` le rejoue sur les 1 004.

### Ce que les sources ne disent pas

Quatre tables, en toutes lettres dans le script pour qu'on puisse les discuter.

**L'auxiliaire**, que Verbiste ne donne pas. La liste des verbes qui prennent
`être` est fermée — mouvement, changement d'état, et tous les pronominaux. Onze
prennent les deux, selon qu'ils ont un complément d'objet : « je suis sorti »,
mais « j'ai sorti la poubelle ». Leur note le dit avec l'exemple.

**Les seize verbes essentiellement pronominaux.** « je souviens » ne se dit pas.
Le lemme s'écrit *se souvenir*, se range à *souvenir*, et la conjugaison porte
le pronom : `je me souviens`, `souviens-toi`, `je me suis souvenu`.

**Les soixante-trois participes invariables.** Un modèle Verbiste décline les
quatre accords, parce qu'un modèle est un jeu de terminaisons ; mais « j'ai
dormi » ne donnera jamais « dormie ». Le modèle ne peut pas le savoir — il est
partagé entre des verbes transitifs et d'autres qui ne le sont pas. La liste
vient des étiquettes de transitivité de Grammalecte.

**Les notes**, quand il y a quelque chose à dire : une case vide, deux formes
concurrentes, un auxiliaire qui hésite. **135 verbes sur 1 004** en ont une. Un
verbe régulier n'en reçoit pas ; le tableau en dit déjà plus.

### Deux sources valent mieux qu'une

Verbiste donne les formes par modèle, Lexique les donne une par une avec leur
étiquette. Les croiser est le seul contrôle qui vaille sur des données qu'on n'a
pas écrites. Il faut trier — Lexique mélange les homographes et propose `pincer`
comme deuxième personne du pluriel de *pouvoir* — mais deux écarts réels sont
ressortis du bruit.

**Sept participes** étaient donnés invariables à tort : la règle du complément
d'objet oubliait l'accord par le sujet et l'emploi adjectival. « La revue est
parue », « les terres émergées », « un projet abouti ».

**Deux modèles** ne donnaient qu'une graphie du futur là où la langue en admet
deux. Verbiste note « je céderai ou je cèderai » pour huit modèles en `é_er`,
mais ne connaît que « je protègerai », et que « je sécherai ». La manquante est
rétablie, l'ancienne devant, comme dans les modèles voisins.

### Ce qu'un verbe irrégulier apprend à un générateur

Le générateur avait quatre verbes réguliers pour toute expérience, et en avait
tiré quatre conclusions fausses.

**Une case peut être vide.** Un temps composé se construisait sur les six
personnes de l'auxiliaire : le passé composé de *falloir* donnait « j'ai
fallu ». C'est le verbe qui décide des cases, pas l'auxiliaire — « il faut » au
présent, donc « il a fallu » et rien d'autre. La case absente s'écrit `null`, et
la page imprime *n'existe pas* plutôt qu'un blanc, qui se lirait comme un oubli.

**Une case peut avoir deux formes.** « je paie » et « je paye » sont toutes deux
correctes. La case en porte la liste, la ligne les montre ensemble, les deux
mots sont cherchables : une case, une ligne, une surbrillance.

**Le participe s'accorde quand l'auxiliaire est `être`.** « nous sommes monté »
n'est pas du français. Avec `avoir` il ne s'accorde pas ici — il ne le ferait
qu'avec un complément d'objet direct placé devant, et un tableau n'en a aucun.

**Un verbe peut n'exister qu'avec son pronom**, qui suit l'élision comme le
reste (`je m'évanouis`) et passe derrière à l'impératif (`souviens-toi`).
L'impératif passé disparaît : « sois-toi souvenu » ne se dit pas non plus.

Et `pris` est le masculin singulier **et** le masculin pluriel de *prendre* : la
même forme dans deux cases. Le tableau ne montrant plus l'accord, les deux
lignes étaient identiques — une seule ligne désormais, mais les deux cases
surlignées.

### Ce que l'échelle a repris

Deux règles justes à quatre verbes deviennent fausses à mille.

`tu` est le participe passé de *taire*. C'est aussi le mot que le générateur
écrit devant chaque case composée, et les citations se cherchaient dans la case
entière : l'entrée `tu` ouvrait **mille tableaux** pour dire que « tu as pris »
contient « tu ». On ne cherche plus que dans la partie verbale de la case —
`as pris`, jamais le sujet qu'on vient d'ajouter.

Et un verbe dont **toutes** les lignes sont citées ne possède pas la forme : il
la tient de son auxiliaire. Ces verbes-là ne sortent plus leur conjugaison ; une
phrase les compte, en tête de l'entrée, avec trois exemples :

> **Auxiliaire** : cette forme construit aussi les temps composés de 957 autres
> verbes du dictionnaire — « il a abandonné », « il a abattu », « il a
> abordé »…

`vécu` ne bouge pas : ses quarante-six lignes sont dans le tableau de *vivre*,
et *vivre* possède la forme. L'entrée `a` passe de **7 Mo à 7 ko**.

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
et c'est ce qui décidait s'il valait la peine d'encoder mille verbes. Il les a
maintenant ; les six mille autres coûtent le même geste, répété.

## Construire

```bash
make            # setup + xml + compilation + installation
make check      # l'analyse est-elle écrite, et juste ?
make verify     # le bundle installé sait-il y répondre ?
make verbe      # le prochain verbe de data/frequence.txt entre (N=10 : dix)
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

Ce n'est plus une estimation sur des verbes synthétiques. Mesuré sur les mille :

| | 4 verbes | 1 004 verbes |
|---|---|---|
| entrées | 162 | 38 917 |
| XML source | 1,2 Mo | 291 Mo |
| **bundle** | 356 ko | **10 Mo** |
| compilation | 1 s | **4 min 27 s** |

Le XML est énorme et le bundle ne l'est pas — vingt-sept fois plus petit. C'est
le découpage par forme qui le veut : chaque forme d'un verbe reçoit sa copie de
la même conjugaison, et quarante copies quasi identiques se compressent entre
elles. Le coût est payé une fois, à la compilation.

Il l'était deux fois plus cher avant qu'on arrête d'ouvrir neuf cent
cinquante-six tableaux sur `ai` : 548 Mo de source, dont la moitié en lignes
d'auxiliaire recopiées.

À 7 011 verbes — tout Verbiste — comptez, au même rythme, une source de deux
gigaoctets et une demi-heure de compilation. C'est le seul vrai mur, et il est
loin.

## Disposition

- `data/verbs.json` — les verbes. Six formes par temps, dans l'ordre
  je / tu / il / nous / vous / ils ; trois pour l'impératif. Une case porte une
  chaîne, une liste quand la langue admet deux formes, ou `null` quand la forme
  n'existe pas.
- `data/frequence.txt` — l'ordre d'entrée : les mille verbes les plus
  fréquents, avec leur fréquence. Engendré depuis Lexique 3, versionné.
- `scripts/import_verbs.py` — l'import. Verbiste pour les formes, Lexique pour
  l'ordre, et quatre tables écrites à la main pour ce que ni l'un ni l'autre ne
  dit : l'auxiliaire, les pronominaux, les participes invariables, les notes.
  `--verifie` relit tout le fichier contre les sources.
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

## Ce qui reste

Les trois manques de la preuve de concept sont comblés : la source libre est
Verbiste, les pronominaux ont leur pronom, le participe s'accorde avec le sujet
quand l'auxiliaire est `être`. Restent ceux-ci.

- **Les six mille autres verbes.** Verbiste en connaît 7 011 ; le classement
  s'arrête à mille parce que c'est ce qui a été relu, pas parce que le
  générateur bute. `make verbe N=100` continue la série.
- **Les verbes occasionnellement pronominaux.** *se laver*, *s'appeler*,
  *se demander* : le dictionnaire les conjugue à la voix active seulement.
  Seize verbes ont le pronom parce qu'ils n'existent pas sans lui ; les autres
  auraient besoin d'un second tableau, pas d'un pronom en plus.
- **L'accord du participe avec le complément d'objet direct placé devant.** Un
  tableau de conjugaison n'en a pas à montrer, donc la question ne se pose pas
  ici — mais c'est elle qu'on cherche quand on hésite sur « les lettres que j'ai
  écrites ».
- **leconjugueur n'est pas une source.** C'est celui du Figaro, et il est
  protégé. Il peut arbitrer une réponse qu'on lui soumet ; il ne peut pas
  fournir de contenu. Même règle que les volumes CLE dans *rappel*.

### Ce que les sources imposent

Verbiste est sous **GPL**, Lexique 3 sous **CC BY-SA**. `data/verbs.json` en
dérive : il en hérite les conditions, et les deux sources se citent. Aucune
n'est commitée — `make verbe` les télécharge dans `data/sources/`, ignoré par
git, comme le Dictionary Development Kit dans `tools/`.
