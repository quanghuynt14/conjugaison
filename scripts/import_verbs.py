#!/usr/bin/env python3
"""Les verbes entrent par ici, un par un, depuis des sources qu'on peut citer.

Écrire mille conjugaisons à la main, c'est mille occasions de se tromper d'un
accent circonflexe. Elles viennent donc de deux fichiers, et de rien d'autre :

- **Verbiste** (Pierre Sarrazin, GPL) pour les formes. `conjugations-fr.xml`
  donne 146 modèles — des terminaisons —, `verbs-fr.xml` rattache chaque verbe
  à son modèle. « parler » plus le modèle « aim:er » donne « je parle ». C'est
  la même méthode qu'un Bescherelle : un tableau, un renvoi.
  On le prend chez verbecc, qui l'entretient : https://github.com/bretttolbert/verbecc
- **Lexique 3.83** (New & Pallier, CC BY-SA) pour l'ordre. Les mille verbes les
  plus fréquents, et « fréquent » veut dire quelque chose de précis : la moyenne
  des fréquences par lemme dans les sous-titres de films et dans les livres.
  http://www.lexique.org

Ce que le script ajoute aux sources tient dans les trois tables ci-dessous :
l'auxiliaire, que Verbiste ne donne pas ; les verbes essentiellement
pronominaux ; et les notes, écrites une par une. Tout le reste est calculé.

Usage :
    python3 scripts/import_verbs.py --classement    # (re)fabrique data/frequence.txt
    python3 scripts/import_verbs.py --add [N]       # ajoute les N verbes suivants
    python3 scripts/import_verbs.py --message VERBE # le message de commit du verbe
    python3 scripts/import_verbs.py --verifie       # relit les verbes déjà écrits
"""

import csv
import json
import pathlib
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import build_xml as B  # noqa: E402  — pour l'élision, les sujets, le pronom

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "verbs.json"
RANKING = ROOT / "data" / "frequence.txt"
CACHE = ROOT / "data" / "sources"

SOURCES = {
    "verbs-fr.xml":
        "https://raw.githubusercontent.com/bretttolbert/verbecc/master/"
        "verbecc/data/xml/verbs/verbs-fr.xml",
    "conjugations-fr.xml":
        "https://raw.githubusercontent.com/bretttolbert/verbecc/master/"
        "verbecc/data/xml/conjugations/conjugations-fr.xml",
    "Lexique383.tsv":
        "http://www.lexique.org/databases/Lexique383/Lexique383.tsv",
}

COMBIEN = 1000  # de verbes à faire entrer, en plus de ceux écrits à la main


# --- ce que les sources ne disent pas ---------------------------------------

# Verbiste donne les formes, pas l'auxiliaire. Il se trouve que la liste des
# verbes qui prennent être est fermée : les verbes de mouvement et de
# changement d'état, plus tous les pronominaux. Partout ailleurs, avoir.
ETRE = {
    "aller", "arriver", "devenir", "entrer", "intervenir", "mourir", "naître",
    "partir", "parvenir", "provenir", "redevenir", "repartir", "rester",
    "retomber", "revenir", "tomber", "venir",
}

# Les deux auxiliaires, selon que le verbe a un complément d'objet direct ou
# non. C'est la même distinction pour tous : « je suis sorti » mais « j'ai sorti
# la poubelle ». On conjugue la construction intransitive, celle qui est
# apparue la première et qu'on entend le plus, et la note dit l'autre.
DOUBLE = {
    "descendre":   ("je suis descendu", "j'ai descendu l'escalier"),
    "entrer":      ("je suis entré", "j'ai entré les données"),
    "monter":      ("je suis monté", "j'ai monté les valises"),
    "passer":      ("je suis passé", "j'ai passé un examen"),
    "redescendre": ("je suis redescendu", "j'ai redescendu les valises"),
    "remonter":    ("je suis remonté", "j'ai remonté la pendule"),
    "rentrer":     ("je suis rentré", "j'ai rentré la voiture"),
    "repasser":    ("je suis repassé", "j'ai repassé la chemise"),
    "ressortir":   ("je suis ressorti", "j'ai ressorti le dossier"),
    "retourner":   ("je suis retourné", "j'ai retourné la crêpe"),
    "sortir":      ("je suis sorti", "j'ai sorti la poubelle"),
}

# Les verbes qui n'existent qu'avec leur pronom. On ne dit pas « je souviens ».
# La liste vient des étiquettes de Grammalecte (Dicollecte), qui les marque
# d'un p ; elle est ici en toutes lettres pour qu'on puisse la lire.
PRONOMINAUX = {
    "accroupir", "agenouiller", "attarder", "efforcer", "emparer", "enfuir",
    "envoler", "évader", "évanouir", "écrier", "écrouler", "marrer", "méfier",
    "réfugier", "souvenir", "suicider",
}

# Verbiste donne le participe passé de fuir pour invariable. Le Robert et le
# Larousse le déclinent, et l'usage tranche : « elle s'est enfuie » s'écrit
# tous les jours. On corrige, et on dit où.
CORRECTIONS = {
    "fuir":   {"participe_passe": ["fui", "fuie", "fuis", "fuies"]},
    "enfuir": {"participe_passe": ["enfui", "enfuie", "enfuis", "enfuies"]},
}

# L'autre écart, et il est de méthode. Un modèle Verbiste décline les quatre
# accords du participe passé, parce qu'un modèle est un jeu de terminaisons et
# que les terminaisons, elles, existent. Mais un verbe qui n'a pas de
# complément d'objet direct n'a rien avec quoi accorder : « j'ai dormi » ne
# donnera jamais « dormie ». Le modèle ne peut pas le savoir — il est partagé
# entre des verbes transitifs et des verbes qui ne le sont pas —, donc c'est
# une liste, et elle est ici.
#
# Elle vient des étiquettes de transitivité de Grammalecte (Dicollecte) : les
# verbes de la série qu'il ne marque pas transitifs directs. On en a retiré
# ceux dont un dictionnaire donne un emploi transitif — hériter une maison, un
# prix convenu, répondre une insolence, obéir, exploser —, parce qu'entre
# afficher une forme de trop et en oublier une, la première se voit.
INVARIABLES = {
    "aboutir", "agir", "appartenir", "bavarder", "bondir", "briller",
    "circuler", "consister", "correspondre", "déconner", "déjeuner",
    "déplaire", "dîner", "disparaître", "divorcer", "dormir", "douter",
    "durer", "émerger", "errer", "être", "exister", "faillir", "fonctionner",
    "frémir", "grouiller", "hésiter", "insister", "jaillir", "jouir", "luire",
    "lutter", "marcher", "mentir", "nuire", "paraître", "participer", "plaire",
    "pleuvoir", "pouvoir", "procéder", "profiter", "progresser", "ramper",
    "réagir", "régner", "ressembler", "résister", "résonner", "retentir",
    "ricaner", "rigoler", "rire", "rôder", "ronfler", "sembler", "sombrer",
    "songer", "sourire", "succéder", "suffire", "surgir", "sursauter",
    "survivre", "tarder", "tousser", "trembler", "tricher", "triompher",
    "voyager",
}

# Les notes écrites à la main. Une note doit apprendre quelque chose : elles
# vont donc aux verbes qui ont une case vide, une forme concurrente, ou un
# auxiliaire qui hésite. Un verbe régulier n'en reçoit pas — il n'y a rien à
# en dire que le tableau ne dise mieux.
NOTES = {
    "être":
        "L'autre auxiliaire. Il sert aux temps composés des verbes de "
        "mouvement et de tous les pronominaux, et à toute la voix passive. Son "
        "participe passé « été » est invariable : rien ne s'accorde avec lui.",
    "pouvoir":
        "Pas d'impératif : on ne commande pas de pouvoir. Le présent a deux "
        "premières personnes, « je peux » et « je puis », la seconde plus "
        "soutenue — mais l'interrogation ne connaît que « puis-je ».",
    "falloir":
        "Verbe impersonnel. Il ne se conjugue qu'à la troisième personne du "
        "singulier, celle du « il » qui ne désigne personne, et il n'a ni "
        "impératif ni participe présent.",
    "pleuvoir":
        "Verbe impersonnel — « il pleut ». Le pluriel existe au figuré, où le "
        "sujet redevient quelqu'un ou quelque chose : « les coups pleuvent ». "
        "Pas d'impératif.",
    "clore":
        "Défectif : ni imparfait, ni passé simple, et le présent perd ses deux "
        "premières personnes du pluriel. On dit « nous fermons » à la place.",
    "foutre":
        "Défectif : pas de passé simple, pas de subjonctif imparfait.",
    "distraire":
        "Comme tous les verbes en -traire : ni passé simple, ni subjonctif "
        "imparfait. « je distrayis » n'existe pas, et rien ne le remplace.",
    "faillir":
        "Pas d'impératif. Le verbe dit ce qui a failli arriver ; on ne "
        "l'ordonne pas.",
    "luire":
        "Deux passés simples coexistent, « il luit » et « il luisit ». Le "
        "participe passé « lui » est invariable.",
    "nuire":
        "Le participe passé « nui » est invariable : nuire se construit avec "
        "à, et un verbe sans complément d'objet direct n'a rien avec quoi "
        "accorder son participe.",
    "asseoir":
        "Trois conjugaisons coexistent, toutes correctes : « j'assieds » et "
        "« j'assois » au présent, « j'assiérai », « j'asseyerai » ou "
        "« j'assoirai » au futur.",
    "demeurer":
        "Avec être au sens de rester : « il est demeuré silencieux ». Avec "
        "avoir au sens d'habiter, qui a vieilli : « il a demeuré vingt ans "
        "rue de Rivoli ».",
    "apparaître":
        "Avec être dans l'usage courant : « il est apparu ». La langue "
        "littéraire garde avoir, qui insiste sur l'événement plutôt que sur "
        "l'état.",
    "convenir":
        "Avec avoir au sens de plaire et de s'accorder : « cela m'a convenu ». "
        "La langue soutenue prend être au sens de tomber d'accord : « nous "
        "sommes convenus de nous revoir ».",
    "accourir":
        "Les deux auxiliaires s'emploient : « il est accouru » regarde le "
        "résultat, « il a accouru » le mouvement.",
}

# Les verbes dont l'auxiliaire n'est pas celui que la table ETRE donnerait,
# parce que la note explique l'hésitation.
AUXILIAIRE_A_LA_MAIN = {"demeurer": "être", "apparaître": "être",
                        "accourir": "être", "convenir": "avoir"}


# --- les sources ------------------------------------------------------------


def source(name):
    """Le fichier, téléchargé une fois. `make setup` fait pareil avec le DDK."""
    path = CACHE / name
    if not path.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        print(f"téléchargement de {name}…", file=sys.stderr)
        urllib.request.urlretrieve(SOURCES[name], path)
    return path


def modeles():
    """nom du modèle -> {(mode, temps) -> [cases]}, une case étant [formes].

    Une case vide dans Verbiste — `<p></p>` — est une forme qui n'existe pas.
    Une case dont la terminaison est vide — `<p><i></i></p>` — est une forme
    égale au radical : le participe passé de nuire est « nui », et « nui » est
    exactement ce qui reste du verbe une fois « re » enlevé. Confondre les deux
    coûterait un participe passé.
    """
    root = ET.parse(source("conjugations-fr.xml")).getroot()
    out = {}
    for modele in root.findall("template"):
        cases = {}
        for mode in modele:
            for temps in mode:
                cases[(mode.tag, temps.tag)] = [
                    [(i.text or "") for i in p.findall("i")]
                    for p in temps.findall("p")
                ]
        out[modele.get("name")] = cases
    return out


def modele_de():
    """verbe -> nom de son modèle."""
    texte = source("verbs-fr.xml").read_text(encoding="utf-8")
    return dict(re.findall(r"<v><i>(.*?)</i><t>(.*?)</t>", texte))


def classement():
    """Les verbes par fréquence décroissante, écrits dans data/frequence.txt.

    Le fichier est engendré une fois et versionné : mille commits n'ont pas à
    relire vingt-cinq mégaoctets de Lexique chacun, et l'ordre de la série se
    lit sans avoir à le refaire.
    """
    connus = modele_de()
    freq = {}
    with source("Lexique383.tsv").open(encoding="utf-8") as f:
        for ligne in csv.DictReader(f, delimiter="\t"):
            if ligne["cgram"] != "VER" or ligne["lemme"] in freq:
                continue
            try:
                films = float(ligne["freqlemfilms2"])
                livres = float(ligne["freqlemlivres"])
            except ValueError:
                continue
            freq[ligne["lemme"]] = (films + livres) / 2
    ordre = sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))
    return [(v, f) for v, f in ordre if v in connus]


def lire_classement():
    lignes = RANKING.read_text(encoding="utf-8").splitlines()
    return [l.split("\t")[0] for l in lignes if l and not l.startswith("#")]


# --- fabriquer un verbe -----------------------------------------------------

TEMPS = {
    "ind.pres":   ("Indicatif", "présent"),
    "ind.imp":    ("Indicatif", "imparfait"),
    "ind.ps":     ("Indicatif", "passé-simple"),
    "ind.fut":    ("Indicatif", "futur-simple"),
    "cond.pres":  ("Conditionnel", "présent"),
    "subj.pres":  ("Subjonctif", "présent"),
    "subj.imp":   ("Subjonctif", "imparfait"),
    "imper.pres": ("Imperatif", "imperatif-présent"),
}

ORDRE_DES_CLES = ["id", "infinitif", "groupe", "auxiliaire", "pronominal",
                  "note", "tenses", "participe_present", "participe_passe"]


def groupe_de(infinitif, participe_present):
    """Le groupe, par la seule règle qui les sépare vraiment.

    Le deuxième groupe n'est pas « les verbes en -ir » : c'est ceux dont le
    participe présent prend -issant. Sans quoi partir, qui donne « partant »,
    y tomberait avec finir, qui donne « finissant ».
    """
    if infinitif == "aller":
        return "3ᵉ groupe"          # le seul verbe en -er du troisième groupe
    if infinitif.endswith("er"):
        return "1ᵉʳ groupe"
    if infinitif.endswith("ir") and (participe_present or "").endswith("issant"):
        return "2ᵉ groupe"
    return "3ᵉ groupe"


def case(radical, formes):
    """[] -> None, une forme -> la chaîne, deux -> la liste."""
    if not formes:
        return None
    if len(formes) == 1:
        return radical + formes[0]
    return [radical + f for f in formes]


def fabrique(infinitif, modele_nom, modeles_):
    """Le verbe au format de data/verbs.json."""
    modele = modeles_[modele_nom]
    terminaison = modele_nom.split(":", 1)[1]
    radical = infinitif[:len(infinitif) - len(terminaison)]

    verbe = {"id": infinitif, "infinitif": infinitif}
    verbe["tenses"] = {
        cle: [case(radical, formes) for formes in modele[position]]
        for cle, position in TEMPS.items()
    }
    verbe["participe_present"] = case(
        radical, modele[("Participe", "participe-présent")][0])
    # Verbiste range le participe passé masculin singulier, masculin pluriel,
    # féminin singulier, féminin pluriel. Ici c'est l'ordre des grammaires —
    # masculin singulier, féminin singulier, masculin pluriel, féminin pluriel.
    pp = [case(radical, formes)
          for formes in modele[("Participe", "participe-passé")]]
    verbe["participe_passe"] = [pp[0], pp[2], pp[1], pp[3]]
    if infinitif in INVARIABLES:
        verbe["participe_passe"] = [pp[0], None, None, None]

    verbe.update(CORRECTIONS.get(infinitif, {}))

    if infinitif in PRONOMINAUX:
        verbe["pronominal"] = True
    verbe["auxiliaire"] = auxiliaire_de(infinitif)
    verbe["groupe"] = groupe_de(infinitif, forme_seule(verbe["participe_present"]))
    note = note_de(verbe)
    if note:
        verbe["note"] = note
    return {cle: verbe[cle] for cle in ORDRE_DES_CLES if cle in verbe}


def auxiliaire_de(infinitif):
    if infinitif in AUXILIAIRE_A_LA_MAIN:
        return AUXILIAIRE_A_LA_MAIN[infinitif]
    if infinitif in PRONOMINAUX or infinitif in ETRE or infinitif in DOUBLE:
        return "être"
    return "avoir"


def forme_seule(cellule):
    """La première forme d'une case, ou None. Pour les calculs, pas l'affichage."""
    formes = B.variants(cellule)
    return formes[0] if formes else None


def exemple(verbe, cle, i):
    """La case telle qu'elle s'affichera : « je me souviens », « j'espérerai »."""
    formes = B.variants(verbe["tenses"][cle][i])
    return [B.with_subject(verbe, cle, i, f) for f in formes]


def note_de(verbe):
    """La note, quand il y a quelque chose à dire.

    Les notes écrites à la main l'emportent. Les autres sortent des données :
    elles ne peuvent donc pas mentir sur les formes, puisqu'elles les citent.
    """
    infinitif = verbe["infinitif"]
    if infinitif in NOTES:
        return NOTES[infinitif]

    morceaux = []

    if infinitif in DOUBLE:
        sans, avec = DOUBLE[infinitif]
        morceaux.append(
            f"Auxiliaire double. Sans complément d'objet, être : « {sans} ». "
            f"Avec un complément d'objet direct, avoir : « {avec} ». Les temps "
            f"composés ci-dessous suivent la première construction.")

    if verbe.get("pronominal"):
        moi = exemple(verbe, "ind.pres", 0)[0]
        morceaux.append(
            f"Verbe essentiellement pronominal : il ne s'emploie qu'avec un "
            f"pronom réfléchi. On dit « {moi} » ; la forme nue ne se conjugue "
            f"pas. Ses temps composés prennent être.")

    doubles = [cle for cle, cases in verbe["tenses"].items()
               if any(isinstance(c, list) for c in cases)]
    if set(doubles) == {"ind.fut", "cond.pres"}:
        a, b = exemple(verbe, "ind.fut", 0)
        morceaux.append(
            f"Depuis les rectifications orthographiques de 1990, le futur et "
            f"le conditionnel s'écrivent aussi avec un accent grave : "
            f"« {a} » ou « {b} ». Les deux sont admises.")
    elif doubles:
        cle = next(c for c in TEMPS if c in doubles)
        i = next(i for i, c in enumerate(verbe["tenses"][cle])
                 if isinstance(c, list))
        formes = exemple(verbe, cle, i)
        morceaux.append(f"Deux conjugaisons également correctes : "
                        f"« {formes[0]} » ou « {formes[1]} ».")

    # Pourquoi cette entrée-là montre une forme là où les autres en montrent
    # quatre. La question se pose en lisant la page ; elle mérite sa phrase.
    if infinitif in INVARIABLES:
        morceaux.append(
            f"Le participe passé « {forme_seule(verbe['participe_passe'][0])} » "
            f"est invariable : le verbe ne prend pas de complément d'objet "
            f"direct, donc rien ne s'accorde avec lui.")

    return " ".join(morceaux) or None


# --- écrire data/verbs.json -------------------------------------------------


def rendu_verbe(verbe):
    """Le verbe en JSON, tel que le fichier est écrit depuis le premier jour :
    une clé par ligne, un temps par ligne, six formes côte à côte."""
    lignes = ["    {"]
    corps = []
    for cle in ORDRE_DES_CLES:
        if cle not in verbe:
            continue
        if cle == "tenses":
            temps = ",\n".join(
                f'        {json.dumps(t, ensure_ascii=False)}: '
                f'{json.dumps(verbe["tenses"][t], ensure_ascii=False)}'
                for t in TEMPS
            )
            corps.append('      "tenses": {\n' + temps + "\n      }")
        else:
            corps.append(f'      {json.dumps(cle, ensure_ascii=False)}: '
                         f'{json.dumps(verbe[cle], ensure_ascii=False)}')
    lignes.append(",\n".join(corps))
    lignes.append("    }")
    return "\n".join(lignes)


def ecrire(data):
    corps = ",\n".join(rendu_verbe(v) for v in data["verbs"])
    DATA.write_text(
        "{\n"
        f'  "_comment": {json.dumps(data["_comment"], ensure_ascii=False)},\n'
        '  "verbs": [\n' + corps + "\n  ]\n}\n",
        encoding="utf-8",
    )


def charger():
    return json.loads(DATA.read_text(encoding="utf-8"))


# --- le message de commit ---------------------------------------------------


def message(verbe, deja, modeles_par_verbe):
    """Ce que ce verbe ajoute au dictionnaire, et rien d'autre.

    Ou bien son modèle y est déjà, et le message nomme le verbe qui l'a
    apporté — « se conjugue comme aimer » est vrai au sens strict : mêmes
    terminaisons, même tableau. Ou bien le modèle est nouveau, et le message
    cite les formes qui le distinguent.
    """
    nom = B.lemma(verbe)
    modele = modeles_par_verbe[verbe["infinitif"]]
    aine = next((v for v in deja
                 if modeles_par_verbe.get(v["infinitif"]) == modele), None)
    if aine is not None:
        comme = f"{nom} : se conjugue comme {B.lemma(aine)}"
        return comme + ", avec le pronom" if verbe.get("pronominal") else comme

    presentes = [i for i in range(6) if B.variants(verbe["tenses"]["ind.pres"][i])]
    citees = [exemple(verbe, "ind.pres", i)[0] for i in presentes[:1] + presentes[3:4]]
    pp = forme_seule(verbe["participe_passe"][0])
    morceaux = [f"« {c} »" for c in citees]
    if pp:
        morceaux.append(f"participe passé « {pp} »")
    return f"{nom} : nouveau modèle — " + ", ".join(morceaux)


# --- entrées ----------------------------------------------------------------


def ajouter(combien):
    data = charger()
    presents = {v["id"] for v in data["verbs"]}
    modeles_ = modeles()
    par_verbe = modele_de()
    attente = [v for v in lire_classement() if v not in presents]

    for infinitif in attente[:combien]:
        verbe = fabrique(infinitif, par_verbe[infinitif], modeles_)
        print(message(verbe, data["verbs"], par_verbe))
        data["verbs"].append(verbe)
    ecrire(data)


def verifier():
    """Ce que l'import produirait pour les verbes déjà écrits.

    Le premier essai a porté sur les quatre verbes écrits à la main avant que
    ce script existe : il fallait qu'il les retrouve, case pour case, sans quoi
    rien ne disait que les mille suivants seraient justes.
    """
    data = charger()
    modeles_ = modeles()
    par_verbe = modele_de()
    ecarts = 0
    for verbe in data["verbs"]:
        refait = fabrique(verbe["infinitif"], par_verbe[verbe["infinitif"]], modeles_)
        for cle in ("tenses", "participe_present", "participe_passe"):
            if refait[cle] != verbe[cle]:
                ecarts += 1
                print(f"  ✗ {verbe['infinitif']} : {cle}")
                print(f"      écrit  {verbe[cle]}")
                print(f"      source {refait[cle]}")
    print(f"{len(data['verbs'])} verbes relus, {ecarts} écart(s)")
    return 1 if ecarts else 0


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    if args[0] == "--classement":
        lignes = [f"# Les {COMBIEN} verbes français les plus fréquents, plus ceux",
                  "# qui étaient déjà là. Source : Lexique 3.83 (lexique.org),",
                  "# moyenne des fréquences par lemme dans les sous-titres de",
                  "# films et dans les livres, par million de mots. Ne sont",
                  "# gardés que les verbes que Verbiste sait conjuguer.",
                  "# verbe\tfréquence"]
        presents = {v["id"] for v in charger()["verbs"]}
        garde = []
        for verbe, f in classement():
            if len(garde) >= COMBIEN + len(presents):
                break
            garde.append((verbe, f))
        lignes += [f"{v}\t{f:.2f}" for v, f in garde]
        RANKING.write_text("\n".join(lignes) + "\n", encoding="utf-8")
        print(f"{RANKING.relative_to(ROOT)} : {len(garde)} verbes")
    elif args[0] == "--add":
        ajouter(int(args[1]) if len(args) > 1 else 1)
    elif args[0] == "--message":
        data = charger()
        par_verbe = modele_de()
        verbe = next(v for v in data["verbs"] if v["id"] == args[1])
        deja = data["verbs"][:data["verbs"].index(verbe)]
        print(message(verbe, deja, par_verbe))
    elif args[0] == "--verifie":
        sys.exit(verifier())
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
