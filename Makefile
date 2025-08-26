#!/usr/bin/make -f
# Makefile for Patchance #
# ---------------------- #
# Created by houston4444
#
PREFIX ?= /usr/local
DESTDIR =
DEST_PATCHANCE := $(DESTDIR)$(PREFIX)/share/patchance

LINK = ln -s -f
LRELEASE ?= lrelease
QT_VERSION ?= 5

# if you set QT_VERSION environment variable to 6 at the make command
# it will choose the other commands QT_API, pyuic6, pylupdate6.
# You will can run patchichi directly in source without install

ifeq ($(QT_VERSION), 6)
	QT_API ?= PyQt6
	PYUIC ?= pyuic6
	PYLUPDATE ?= pylupdate6
	ifeq (, $(shell which $(LRELEASE)))
		LRELEASE := lrelease-qt6
	endif
else
    QT_API ?= PyQt5
	PYUIC ?= pyuic5
	PYLUPDATE ?= pylupdate5
	ifeq (, $(shell which $(LRELEASE)))
		LRELEASE := lrelease-qt5
	endif
endif

# neeeded for make install
BUILD_CFG_FILE := src/qt_api.py
QT_API_INST := $(shell grep ^QT_API= $(BUILD_CFG_FILE) 2>/dev/null| cut -d'=' -f2| cut -d"'" -f2)
QT_API_INST ?= PyQt5

ICON_SIZES := 16 24 32 48 64 96 128 256

PYTHON := python3
ifeq (, $(shell which $(PYTHON)))
  PYTHON := python
endif

PATCHBAY_DIR=HoustonPatchbay

# ---------------------

all: PATCHBAY QT_PREPARE UI RES LOCALE

PATCHBAY:
	@(cd $(PATCHBAY_DIR) && $(MAKE))

# ---------------------
# Resources

QT_PREPARE:
	$(info compiling for Qt$(QT_VERSION) using $(QT_API))
	$(file > $(BUILD_CFG_FILE),QT_API='$(QT_API)')

    ifeq ($(QT_API), $(QT_API_INST))
    else
		rm -f *~ src/*~ src/*.pyc src/ui/*.py \
		    resources/locale/*.qm src/resources_rc.py
    endif
	install -d src/ui

RES: src/resources_rc.py

src/resources_rc.py: resources/resources.qrc
	rcc -g python $< |sed 's/ PySide. / qtpy /' > $@

# ---------------------
# UI code

UI: $(shell \
	ls resources/ui/*.ui| sed 's|\.ui$$|.py|'| sed 's|^resources/|src/|')

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

    # Copy patchbay themes, manual and lib
	cp -r HoustonPatchbay/themes $(DEST_PATCHANCE)/$(PATCHBAY_DIR)/
	cp -r HoustonPatchbay/manual $(DEST_PATCHANCE)/$(PATCHBAY_DIR)/
	cp -r HoustonPatchbay/source $(DEST_PATCHANCE)/$(PATCHBAY_DIR)/

# 	# Install main code
	cp -r src $(DEST_PATCHANCE)/
	
# 	# compile python files
	$(PYTHON) -m compileall $(DEST_PATCHANCE)/HoustonPatchbay/source/
	$(PYTHON) -m compileall $(DEST_PATCHANCE)/src/
	
# 	# install local manual
# 	cp -r manual $(DEST_PATCHANCE)/
		
#   # install main bash scripts to bin
	install -m 755 data/bin/patchance  $(DESTDIR)$(PREFIX)/bin/

# 	# Install Translations
	install -m 644 locale/*.qm $(DEST_PATCHANCE)/locale/
	install -m 644 $(PATCHBAY_DIR)/locale/*.qm $(DEST_PATCHANCE)/$(PATCHBAY_DIR)/locale/

uninstall:
	rm -f $(DESTDIR)$(PREFIX)/bin/patchance
	rm -f $(DESTDIR)$(PREFIX)/share/applications/patchance.desktop
	rm -f $(DESTDIR)$(PREFIX)/share/icons/hicolor/*/apps/patchance.png
	rm -f $(DESTDIR)$(PREFIX)/share/icons/hicolor/scalable/apps/patchance.svg
	rm -rf $(DEST_PATCHANCE)
