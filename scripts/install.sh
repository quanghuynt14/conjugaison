#!/bin/sh
#
# Installe le dictionnaire Conjugaison française sur ce Mac.
#
#   curl -fsSL https://raw.githubusercontent.com/quanghuynt14/conjugaison/HEAD/scripts/install.sh | sh
#
# ou, si l'archive est déjà là :
#
#   sh install.sh                 l'archive posée à côté
#   sh install.sh ~/Downloads     l'archive d'un autre dossier
#
# Rien à compiler : un bundle .dictionary est un dossier de données, pas un
# programme. Ni Python, ni le DDK, ni Rosetta, ni Verbiste, ni les vingt-cinq
# mégaoctets de Lexique — tout ça ne sert qu'à *fabriquer* le dictionnaire.
#
# /bin/sh et non bash : un script fait pour être tubé ne choisit pas le shell
# dans lequel il tombe.

set -eu

REPO="quanghuynt14/conjugaison"
ASSET="conjugaison.dictionary.zip"
DEST="$HOME/Library/Dictionaries"
SOURCE_DIR="${1:-}"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT INT TERM

# --- où est l'archive -------------------------------------------------------

if [ -z "$SOURCE_DIR" ]; then
  # Tubé depuis curl : $0 ne désigne aucun dossier utile. Sinon, on regarde à
  # côté du script.
  case "${0:-}" in
    */*) here="$(cd "$(dirname "$0")" && pwd)" ;;
    *)   here="" ;;
  esac
  if [ -n "$here" ] && ls "$here"/*.dictionary.zip >/dev/null 2>&1; then
    SOURCE_DIR="$here"
  fi
fi

if [ -z "$SOURCE_DIR" ]; then
  SOURCE_DIR="$tmp/dl"
  mkdir -p "$SOURCE_DIR"
  echo "  Téléchargement de la dernière version…"

  if ! curl -fsSL -o "$SOURCE_DIR/$ASSET" \
      "https://github.com/$REPO/releases/latest/download/$ASSET"; then
    cat >&2 <<ERR

  Téléchargement impossible : $ASSET

  Vérifiez la connexion, ou prenez l'archive à la main sur
  https://github.com/$REPO/releases/latest puis relancez :

      sh install.sh ~/Downloads

ERR
    exit 1
  fi
fi

# --- installation -----------------------------------------------------------

found=0
mkdir -p "$DEST"

for zip in "$SOURCE_DIR"/*.dictionary.zip; do
  [ -e "$zip" ] || continue
  found=1

  rm -rf "$tmp/x"
  mkdir -p "$tmp/x"
  ditto -x -k "$zip" "$tmp/x"

  # Le nom d'installation vient du bundle **dans** l'archive, jamais du nom du
  # fichier : l'archive doit survivre à GitHub, le dictionnaire doit garder son
  # nom.
  bundle="$(find "$tmp/x" -maxdepth 2 -name '*.dictionary' -print -quit)"
  [ -d "$bundle" ] || { echo "  ✗ pas de bundle dans $(basename "$zip")" >&2; continue; }
  name="$(basename "$bundle")"
  echo "  → $name"

  # Un fichier téléchargé porte l'attribut de quarantaine. Dictionary.app lit
  # quand même — ce ne sont pas des exécutables — mais l'enlever évite une
  # question à laquelle personne ne saura répondre.
  xattr -dr com.apple.quarantine "$bundle" 2>/dev/null || true

  # `rm -rf` avant `ditto`, et ce n'est pas une précaution de style : copier
  # par-dessus un bundle déjà en place laisse macOS avec un index périmé. Le
  # dictionnaire continue de répondre à l'API et disparaît de la fenêtre de
  # consultation. C'est la panne qui a coûté trois fausses pistes ici même —
  # plist, langue déclarée, index de référence — alors que réinstaller
  # proprement suffisait.
  rm -rf "$DEST/$name"
  ditto --noextattr --norsrc "$bundle" "$DEST/$name"
done

if [ "$found" -eq 0 ]; then
  echo "Aucun *.dictionary.zip dans $SOURCE_DIR" >&2
  exit 1
fi

touch "$DEST"

# `killall LookupViewService` ne marche pas : ce sont des services XPC, killall
# ne les reconnaît pas et sort sans rien dire. Il en tourne un par application
# hôte, chacun gardant la liste des dictionnaires pour toute sa durée de vie —
# on en a trouvé deux vieux de la veille. C'est ce qui a fait croire pendant
# toute une séance que les corrections n'avaient aucun effet.
pkill -9 -f LookupViewService >/dev/null 2>&1 || true
pkill -9 -f DictionaryServiceHelper >/dev/null 2>&1 || true
killall cfprefsd >/dev/null 2>&1 || true

cat <<'MSG'

  Installé dans ~/Library/Dictionaries.

  Il reste une chose, et aucun script ne peut la faire à votre place :
  ouvrez Dictionnaire.app > Réglages, cochez « Conjugaison française »,
  et remontez-la au-dessus des dictionnaires d'Apple.

  Cherchez ensuite « fasse », ou « vis », ou « eussent ».
MSG
