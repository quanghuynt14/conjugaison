DICT_NAME           = Conjugaison
DICT_SRC_PATH       = src/conjugaison.xml
CSS_PATH            = src/conjugaison.css
PLIST_PATH          = src/Info.plist

DDK_DIR             = tools/dictionary-development-kit
DDK_BIN             = $(DDK_DIR)/bin
DDK_REPO            = https://github.com/SebastianSzturo/Dictionary-Development-Kit.git

DICT_DEV_KIT_OBJ_DIR = ./objects
export DICT_DEV_KIT_OBJ_DIR

DESTINATION_FOLDER  = $(HOME)/Library/Dictionaries

.PHONY: all xml build install uninstall setup clean check verify refresh verbe dist release

all: install

# Apple's build tools are x86_64 only, so an Apple Silicon Mac needs Rosetta 2:
#   softwareupdate --install-rosetta --agree-to-license
setup:
	@test -d $(DDK_DIR) || git clone --depth 1 $(DDK_REPO) $(DDK_DIR)
	@chmod +x $(DDK_BIN)/* 2>/dev/null || true
	@echo "DDK prêt dans $(DDK_DIR)."

xml:
	python3 scripts/build_xml.py

# Le prochain verbe de data/frequence.txt entre dans data/verbs.json, avec ses
# formes prises dans Verbiste. `make verbe N=10` en fait entrer dix. Le
# classement lui-même se refait par `python3 scripts/import_verbs.py
# --classement`, qui a besoin des vingt-cinq mégaoctets de Lexique.
N ?= 1
verbe:
	python3 scripts/import_verbs.py --add $(N)

# -v 10.11 : la disposition moderne du bundle — données sous Contents/Resources,
# index trie, IDXDictionaryVersion 3. Sans elle, build_dict.sh vise 10.5 par défaut
# et écrit un bundle que les macOS récents ne lisent plus.
#
# preserve_unused_ref_id_in_reference_index : par défaut le DDK ne met dans
# l'index de référence que les entrées *citées* par un lien ou par le front
# matter. Nous n'avons ni l'un ni l'autre, donc cet index sortait vide — le build
# le disait à chaque fois, « No reference index record », et la fenêtre de
# consultation, qui résout l'entrée par son identifiant, retombait sur la
# première du fichier : « a », c'est-à-dire avoir, quelle que soit la recherche.
#
# Le DDK signale l'index vide et continue. On en fait une erreur : c'est une
# panne invisible partout sauf dans une fenêtre qu'aucun script n'ouvre.
build: setup xml
	@preserve_unused_ref_id_in_reference_index=1 \
		"$(DDK_BIN)/build_dict.sh" -v 10.11 $(DICT_NAME) $(DICT_SRC_PATH) \
		$(CSS_PATH) $(PLIST_PATH) 2>&1 | tee $(DICT_DEV_KIT_OBJ_DIR)-build.log
	@if grep -q "No reference index record" $(DICT_DEV_KIT_OBJ_DIR)-build.log; then \
		echo; \
		echo "ERREUR : index de référence vide. La fenêtre de consultation"; \
		echo "affichera la première entrée du fichier pour toute recherche."; \
		exit 1; \
	fi

# Le `rm -rf` n'est pas une précaution de style. `ditto` par-dessus un bundle
# déjà en place laisse macOS avec un index périmé : le dictionnaire continue de
# répondre à l'API et disparaît de la fenêtre de consultation. C'est ce qui a
# coûté trois fausses pistes — plist, langue, index de référence — alors que
# réinstaller proprement suffisait.
install: build
	mkdir -p $(DESTINATION_FOLDER)
	rm -rf $(DESTINATION_FOLDER)/$(DICT_NAME).dictionary
	ditto --noextattr --norsrc \
		$(DICT_DEV_KIT_OBJ_DIR)/$(DICT_NAME).dictionary \
		$(DESTINATION_FOLDER)/$(DICT_NAME).dictionary
	touch $(DESTINATION_FOLDER)
	@$(MAKE) --no-print-directory refresh
	@echo
	@echo "Installé. Relancez Dictionary.app, puis Réglages > Sources et cochez"
	@echo "« Conjugaison française ». Cherchez ensuite « fasse »."

# `killall LookupViewService` ne marche pas : ce sont des services XPC, killall
# ne les reconnaît pas et sort sans rien dire. Il y en a un par application
# hôte, chacun garde la liste des dictionnaires pour toute sa durée de vie, et
# on en a trouvé deux vieux de la veille. C'est ce qui a fait croire pendant
# toute une séance que les corrections n'avaient aucun effet.
refresh:
	@pkill -9 -f LookupViewService 2>/dev/null || true
	@pkill -9 -f DictionaryServiceHelper 2>/dev/null || true
	@killall cfprefsd 2>/dev/null || true
	@echo "Services de consultation relancés."

uninstall:
	rm -rf $(DESTINATION_FOLDER)/$(DICT_NAME).dictionary
	@echo "Désinstallé. Relancez Dictionary.app."

# check  : la forme est-elle écrite dans le XML ?
# verify : le bundle installé sait-il y répondre ? C'est celui qui compte.
check: xml
	python3 scripts/check.py

verify:
	python3 scripts/verify_lookup.py

# --- distribution ---------------------------------------------------------
#
# Un bundle .dictionary est un dossier de données : il se copie d'un Mac à
# l'autre tel quel. Rien à compiler en face — le DDK, Python, Rosetta, Verbiste
# et les vingt-cinq mégaoctets de Lexique ne servent qu'à le *fabriquer*.
#
# `ditto -c -k` plutôt que `zip` : c'est l'outil d'Apple, il préserve ce qu'un
# bundle attend, et c'est le pendant exact du `ditto -x -k` de install.sh.
#
# L'archive porte un nom en minuscules sans accent. GitHub remplace tout
# caractère non-ASCII du nom d'un fichier de version par un point, et l'URL de
# téléchargement rend alors 404 ; « Conjugaison » y échappe, mais autant que la
# règle soit la même dans les deux dépôts.
DIST  = dist
ASSET = conjugaison.dictionary.zip

dist:
	@test -d "$(DESTINATION_FOLDER)/$(DICT_NAME).dictionary" || \
		{ echo "✗ $(DICT_NAME).dictionary pas installé — lancez make install"; exit 1; }
	@mkdir -p $(DIST)
	@rm -f "$(DIST)/$(ASSET)"
	@ditto -c -k --sequesterRsrc --keepParent \
		"$(DESTINATION_FOLDER)/$(DICT_NAME).dictionary" "$(DIST)/$(ASSET)"
	@cp scripts/install.sh $(DIST)/
	@printf "  %-28s %5.1f Mo\n" "$(ASSET)" \
		$$(echo "$$(stat -f %z "$(DIST)/$(ASSET)")/1000000" | bc -l)
	@echo "  → $(DIST)/  (l'archive et install.sh)"

# Une version sur GitHub, pour que l'installation tienne en une ligne.
release: dist
	@v=$$(date +%Y.%m.%d); \
	gh release create "v$$v" $(DIST)/$(ASSET) $(DIST)/install.sh \
		--title "Conjugaison $$v" \
		--notes "Conjugaison inversée pour Dictionary.app." \
		|| gh release upload "v$$v" $(DIST)/$(ASSET) $(DIST)/install.sh --clobber

clean:
	rm -rf $(DICT_DEV_KIT_OBJ_DIR) $(DIST) src/conjugaison.xml
