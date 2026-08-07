# Conjugaison

## Référence

**James Somers, « You're probably using the wrong dictionary » —
https://jsomers.net/blog/dictionary**

L'article de référence du projet. À relire avant toute décision sur ce à quoi
une entrée doit ressembler, ou sur la façon dont un dictionnaire tiers entre
dans Dictionary.app.

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

websters-1913 sert déjà de témoin dans ce dépôt — c'est le dictionnaire tiers
avec lequel on compare quand une pièce du bundle a l'air anormale (l'index de
référence, par exemple).
