#!/usr/bin/make -f
# Makefile for Patchance #
# ---------------------- #
# Created by houston4444
#
PREFIX ?= /usr/local
DESTDIR =
DEST_PATCHANCE := $(DESTDIR)$(PREFIX)/share/patchance

LINK = ln -s -f
PYUIC := pyuic5
PYRCC := pyrcc5

LRELEASE := lrelease
ifeq (, $(shell which $(LRELEASE)))
 LRELEASE := lrelease-qt5
endif

ifeq (, $(shell which $(LRELEASE)))
 LRELEASE := lrelease-qt4
endif

PYTHON := python3
ifeq (, $(shell which $(PYTHON)))
  PYTHON := python
endif

PATCHBAY_DIR=HoustonPatchbay

# ---------------------

all: PATCHBAY UI RES LOCALE

PATCHBAY:
	@(cd $(PATCHBAY_DIR) && $(MAKE))

# ---------------------
# Resources

RES: src/resources_rc.py

src/resources_rc.py: resources/resources.qrc
	$(PYRCC) $< -o $@

# ---------------------
# UI code

UI: mkdir_ui patchance 

mkdir_ui:
	@if ! [ -e src/ui ];then mkdir -p src/ui; fi

patchance: src/ui/main_win.py \
		   src/ui/about_patchance.py

src/ui/%.py: resources/ui/%.ui
	$(PYUIC) $< -o $@
	
PY_CACHE:
	$(PYTHON) -m compileall src/
	
# ------------------------
# # Translations Files

LOCALE: locale

locale: locale/patchance_en.qm \
		locale/patchance_fr.qm \

locale/%.qm: locale/%.ts
	$(LRELEASE) $< -qm $@

# -------------------------

clean:
	@(cd $(PATCHBAY_DIR) && $(MAKE) $@)
	rm -f *~ src/*~ src/*.pyc  locale/*.qm src/resources_rc.py
	rm -f -R src/ui
	rm -f -R src/__pycache__ src/*/__pycache__ src/*/*/__pycache__ \
		  src/*/*/*/__pycache__

# -------------------------

debug:
	$(MAKE) DEBUG=true

# -------------------------

install:
# 	# Create directories
	install -d $(DESTDIR)$(PREFIX)/bin/
	install -d $(DESTDIR)$(PREFIX)/share/
	install -d $(DESTDIR)$(PREFIX)/share/icons/hicolor/16x16/apps/
	install -d $(DESTDIR)$(PREFIX)/share/icons/hicolor/24x24/apps/
	install -d $(DESTDIR)$(PREFIX)/share/icons/hicolor/32x32/apps/
	install -d $(DESTDIR)$(PREFIX)/share/icons/hicolor/48x48/apps/
	install -d $(DESTDIR)$(PREFIX)/share/icons/hicolor/64x64/apps/
	install -d $(DESTDIR)$(PREFIX)/share/icons/hicolor/96x96/apps/
	install -d $(DESTDIR)$(PREFIX)/share/icons/hicolor/128x128/apps/
	install -d $(DESTDIR)$(PREFIX)/share/icons/hicolor/256x256/apps/
	install -d $(DESTDIR)$(PREFIX)/share/icons/hicolor/scalable/apps/
	install -d $(DESTDIR)$(PREFIX)/share/applications/
	install -d $(DEST_PATCHANCE)/
	install -d $(DEST_PATCHANCE)/locale/
	install -d $(DEST_PATCHANCE)/$(PATCHBAY_DIR)/
	install -d $(DEST_PATCHANCE)/$(PATCHBAY_DIR)/locale
	
# 	# Copy Desktop Files
	install -m 644 data/share/applications/*.desktop \
		$(DESTDIR)$(PREFIX)/share/applications/

# 	# Install icons
	install -m 644 resources/main_icon/16x16/patchance.png   \
		$(DESTDIR)$(PREFIX)/share/icons/hicolor/16x16/apps/
	install -m 644 resources/main_icon/24x24/patchance.png   \
		$(DESTDIR)$(PREFIX)/share/icons/hicolor/24x24/apps/
	install -m 644 resources/main_icon/32x32/patchance.png   \
		$(DESTDIR)$(PREFIX)/share/icons/hicolor/32x32/apps/
	install -m 644 resources/main_icon/48x48/patchance.png   \
		$(DESTDIR)$(PREFIX)/share/icons/hicolor/48x48/apps/
	install -m 644 resources/main_icon/64x64/patchance.png   \
		$(DESTDIR)$(PREFIX)/share/icons/hicolor/64x64/apps/
	install -m 644 resources/main_icon/96x96/patchance.png   \
		$(DESTDIR)$(PREFIX)/share/icons/hicolor/96x96/apps/
	install -m 644 resources/main_icon/128x128/patchance.png \
		$(DESTDIR)$(PREFIX)/share/icons/hicolor/128x128/apps/
	install -m 644 resources/main_icon/256x256/patchance.png \
		$(DESTDIR)$(PREFIX)/share/icons/hicolor/256x256/apps/

# 	# Install icons, scalable
	install -m 644 resources/main_icon/scalable/patchance.svg \
		$(DESTDIR)$(PREFIX)/share/icons/hicolor/scalable/apps/

	# Copy patchbay themes
	cp -r HoustonPatchbay/themes $(DEST_PATCHANCE)/$(PATCHBAY_DIR)/

# 	# Install main code
	cp -r src $(DEST_PATCHANCE)/
	rm $(DEST_PATCHANCE)/src/patchbay
	cp -r $(PATCHBAY_DIR)/patchbay $(DEST_PATCHANCE)/src/
	
# 	# compile python files
	$(PYTHON) -m compileall $(DEST_PATCHANCE)/src/
	
# 	# install local manual
# 	cp -r manual $(DEST_PATCHANCE)/
		
#   # install main bash scripts to bin
	install -m 755 data/patchance  $(DESTDIR)$(PREFIX)/bin/
	sed -i "s?X-PREFIX-X?$(PREFIX)?" $(DESTDIR)$(PREFIX)/bin/patchance

# 	# Install Translations
	install -m 644 locale/*.qm $(DEST_PATCHANCE)/locale/
	install -m 644 $(PATCHBAY_DIR)/locale/*.qm $(DEST_PATCHANCE)/$(PATCHBAY_DIR)/locale/

uninstall:
	rm -f $(DESTDIR)$(PREFIX)/bin/patchance
	rm -f $(DESTDIR)$(PREFIX)/share/applications/patchance.desktop
	rm -f $(DESTDIR)$(PREFIX)/share/icons/hicolor/*/apps/patchance.png
	rm -f $(DESTDIR)$(PREFIX)/share/icons/hicolor/scalable/apps/patchance.svg
	rm -rf $(DEST_PATCHANCE)
