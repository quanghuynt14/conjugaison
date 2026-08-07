# Conjugaison

## Références

### L'article — https://jsomers.net/blog/dictionary

James Somers, « You're probably using the wrong dictionary ». L'article de
référence du projet. À relire avant toute décision sur ce à quoi une entrée
doit ressembler, ou sur la façon dont un dictionnaire tiers entre dans
Dictionary.app.

Ce qu'on y trouve :

- **L'argument.** Une définition doit apprendre quelque chose, pas paraphraser.
  Somers oppose la prose de Webster 1913 à la platitude du New Oxford American.
  C'est la barre à tenir pour le corps d'une entrée.
- **Le chemin d'installation.** Webster 1913 converti depuis StarDict par
  DictUnifier, puis déposé dans `~/Library/Dictionaries/`, coché dans les
  réglages, remonté en tête pour passer devant les dictionnaires d'Apple. Même
  emplacement et mêmes réglages que `make install` ici.
- **Le bundle Apple Silicon** : https://github.com/ponychicken/WebsterParser
  (les binaires du DDK, eux, restent x86_64 — Rosetta 2 obligatoire).
- **Le correctif CSS** (`p { line-height: 0.7em }` dans `DefaultStyle.css`) :
  un dictionnaire converti sort typographiquement faux, et la feuille de style
  du bundle est là pour ça. `src/conjugaison.css` joue le même rôle.

### Le bundle — https://github.com/cmod/websters-1913

Webster 1913 empaqueté et restylé pour Dictionary.app. Le contenu vient du
parseur de ponychicken ; ce dépôt-ci n'ajoute que la CSS, et son auteur le dit
en toutes lettres. Donc : pas de Makefile, pas de DDK, aucun réglage de
compilation à y chercher. Ce qu'on y prend, c'est un `.dictionary` construit et
qui marche.

Deux usages :

- **Témoin.** C'est le bundle avec lequel on compare quand une pièce du nôtre a
  l'air anormale. C'est comme ça qu'on a su qu'un `EntryID.index` vide était un
  défaut : le sien est peuplé.
- **Modèle typographique.** Un dictionnaire lu dans une petite fenêtre est un
  problème de CSS avant d'être un problème de données. `src/conjugaison.css`
  répond à la même question.
