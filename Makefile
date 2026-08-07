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

.PHONY: all xml build install uninstall setup clean check verify

all: install

# Apple's build tools are x86_64 only, so an Apple Silicon Mac needs Rosetta 2:
#   softwareupdate --install-rosetta --agree-to-license
setup:
	@test -d $(DDK_DIR) || git clone --depth 1 $(DDK_REPO) $(DDK_DIR)
	@chmod +x $(DDK_BIN)/* 2>/dev/null || true
	@echo "DDK prêt dans $(DDK_DIR)."

xml:
	python3 scripts/build_xml.py

# -v 10.11 : la disposition moderne du bundle — données sous Contents/Resources,
# index trie, IDXDictionaryVersion 3. Sans elle, build_dict.sh vise 10.5 par défaut
# et écrit un bundle que les macOS récents ne lisent plus.
build: setup xml
	"$(DDK_BIN)/build_dict.sh" -v 10.11 $(DICT_NAME) $(DICT_SRC_PATH) $(CSS_PATH) $(PLIST_PATH)

install: build
	mkdir -p $(DESTINATION_FOLDER)
	ditto --noextattr --norsrc \
		$(DICT_DEV_KIT_OBJ_DIR)/$(DICT_NAME).dictionary \
		$(DESTINATION_FOLDER)/$(DICT_NAME).dictionary
	touch $(DESTINATION_FOLDER)
	@echo
	@echo "Installé. Relancez Dictionary.app, puis Réglages > Sources et cochez"
	@echo "« Conjugaison française ». Cherchez ensuite « fasse »."

uninstall:
	rm -rf $(DESTINATION_FOLDER)/$(DICT_NAME).dictionary
	@echo "Désinstallé. Relancez Dictionary.app."

# check  : la forme est-elle écrite dans le XML ?
# verify : le bundle installé sait-il y répondre ? C'est celui qui compte.
check: xml
	python3 scripts/check.py

verify:
	python3 scripts/verify_lookup.py

clean:
	rm -rf $(DICT_DEV_KIT_OBJ_DIR) src/conjugaison.xml
