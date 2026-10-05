# Conjugaison

Une conjugaison inversée pour Dictionary.app, sur macOS. Vous tapez une forme,
il vous dit de quel verbe elle vient, et à quel temps.

Sélectionnez `vis` n'importe où, faites ⌃⌘D :

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

Suit la conjugaison complète des deux verbes, la forme surlignée.

**2 004 verbes**, les plus fréquents du français. 77 277 formes.

## Installer

```bash
curl -fsSL https://raw.githubusercontent.com/quanghuynt14/conjugaison/HEAD/scripts/install.sh | sh
```

Dix mégaoctets. Rien à compiler.

Puis, une seule fois :

1. Ouvrez **Dictionnaire.app**.
2. **Dictionnaire › Réglages** (⌘,).
3. Cochez **Conjugaison française** et montez-la en tête.

Essayez `vis`, `fasse`, `faites`, `souviens`, `faut`, `pris`.

### Hors ligne

Téléchargez `conjugaison.dictionary.zip` depuis la
[dernière version](https://github.com/quanghuynt14/conjugaison/releases/latest),
puis :

```bash
sh install.sh ~/Downloads
```

### Désinstaller

```bash
rm -rf ~/Library/Dictionaries/Conjugaison.dictionary
```

## À côté

[**dictionnaire**](https://github.com/quanghuynt14/dictionnaire) donne le
*sens*, du français et de l'anglais vers le vietnamien. Les deux cohabitent :
`allions` ouvre sa conjugaison ici, sa traduction là.

## Construire

Inutile pour s'en servir. Utile pour ajouter des verbes.

Il faut Python 3, et Rosetta 2 sur Apple Silicon : le kit d'Apple est en x86_64.

```bash
make            # compile et installe
make check      # relit le XML
make verify     # interroge le bundle installé
make verbe N=10 # ajoute les dix verbes suivants par fréquence
make dist       # fabrique l'archive
```

## Sources

- **[Verbiste](https://github.com/bretttolbert/verbecc)** (GPL) pour les formes.
- **[Lexique 3.83](http://www.lexique.org)** (CC BY-SA) pour l'ordre de fréquence.

`data/verbs.json` en dérive et hérite de leurs licences.

## Pour aller plus loin

[`docs/conception.md`](docs/conception.md) raconte les choix et les pannes :
pourquoi une entrée par forme, ce que les sources ne disent pas, pourquoi
réinstaller par-dessus casse la fenêtre de consultation.
