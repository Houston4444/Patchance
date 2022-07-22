#!/usr/bin/make -f
# Makefile for RaySession #
# ---------------------- #
# Created by houston4444
#
PREFIX ?= /usr/local
DESTDIR =
DEST_RAY := $(DESTDIR)$(PREFIX)/share/patchance

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

all: PATCHBAY UI RES

PATCHBAY:
	@(cd $(PATCHBAY_DIR) && $(MAKE))

# ---------------------
# Resources

RES: resources_rc.py

resources_rc.py: resources/resources.qrc
	$(PYRCC) $< -o $@

# ---------------------
# UI code

UI: mkdir_ui patchance 

mkdir_ui:
	@if ! [ -e src/ui ];then mkdir -p src/ui; fi

patchance: src/ui/main_win.py

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
	rm -f *~ src/*~ src/*.pyc  locale/*.qm
	rm -f -R src/ui
	rm -f -R src/__pycache__ src/*/__pycache__ src/*/*/__pycache__ \
		  src/*/*/*/__pycache__

# -------------------------

debug:
	$(MAKE) DEBUG=true

# -------------------------

# install:
# 	# Create directories
# 	install -d $(DESTDIR)$(PREFIX)/bin/
# 	install -d $(DESTDIR)$(PREFIX)/share/applications/
# 	install -d $(DESTDIR)$(PREFIX)/share/icons/hicolor/16x16/apps/
# 	install -d $(DESTDIR)$(PREFIX)/share/icons/hicolor/24x24/apps/
# 	install -d $(DESTDIR)$(PREFIX)/share/icons/hicolor/32x32/apps/
# 	install -d $(DESTDIR)$(PREFIX)/share/icons/hicolor/48x48/apps/
# 	install -d $(DESTDIR)$(PREFIX)/share/icons/hicolor/64x64/apps/
# 	install -d $(DESTDIR)$(PREFIX)/share/icons/hicolor/96x96/apps/
# 	install -d $(DESTDIR)$(PREFIX)/share/icons/hicolor/128x128/apps/
# 	install -d $(DESTDIR)$(PREFIX)/share/icons/hicolor/256x256/apps/
# 	install -d $(DESTDIR)$(PREFIX)/share/icons/hicolor/scalable/apps/
# 	install -d $(DEST_RAY)/
# 	install -d $(DEST_RAY)/locale/
# 	install -d $(DESTDIR)/etc/xdg/
# 	install -d $(DESTDIR)/etc/xdg/raysession/
# 	install -d $(DESTDIR)/etc/xdg/raysession/client_templates/
	
# 	# Copy Templates Factory
# 	cp -r client_templates/40_ray_nsm  $(DESTDIR)/etc/xdg/raysession/client_templates/
# 	cp -r client_templates/60_ray_lash $(DESTDIR)/etc/xdg/raysession/client_templates/
# 	cp -r client_templates  $(DEST_RAY)/
# 	cp -r session_templates $(DEST_RAY)/
# 	cp -r session_scripts   $(DEST_RAY)/
# 	cp -r data              $(DEST_RAY)/
# 	cp -r patchbay_themes   $(DEST_RAY)/
	
# 	# Copy Desktop Files
# 	install -m 644 data/share/applications/*.desktop \
# 		$(DESTDIR)$(PREFIX)/share/applications/

# 	# Install icons
# 	install -m 644 resources/main_icon/16x16/raysession.png   \
# 		$(DESTDIR)$(PREFIX)/share/icons/hicolor/16x16/apps/
# 	install -m 644 resources/main_icon/24x24/raysession.png   \
# 		$(DESTDIR)$(PREFIX)/share/icons/hicolor/24x24/apps/
# 	install -m 644 resources/main_icon/32x32/raysession.png   \
# 		$(DESTDIR)$(PREFIX)/share/icons/hicolor/32x32/apps/
# 	install -m 644 resources/main_icon/48x48/raysession.png   \
# 		$(DESTDIR)$(PREFIX)/share/icons/hicolor/48x48/apps/
# 	install -m 644 resources/main_icon/64x64/raysession.png   \
# 		$(DESTDIR)$(PREFIX)/share/icons/hicolor/64x64/apps/
# 	install -m 644 resources/main_icon/96x96/raysession.png   \
# 		$(DESTDIR)$(PREFIX)/share/icons/hicolor/96x96/apps/
# 	install -m 644 resources/main_icon/128x128/raysession.png \
# 		$(DESTDIR)$(PREFIX)/share/icons/hicolor/128x128/apps/
# 	install -m 644 resources/main_icon/256x256/raysession.png \
# 		$(DESTDIR)$(PREFIX)/share/icons/hicolor/256x256/apps/

# 	# Install icons, scalable
# 	install -m 644 resources/main_icon/scalable/raysession.svg \
# 		$(DESTDIR)$(PREFIX)/share/icons/hicolor/scalable/apps/

# 	# Install main code
# 	cp -r src $(DEST_RAY)/
# 	rm $(DEST_RAY)/src/gui/patchbay
# 	cp -r $(PATCHBAY_DIR)/patchbay $(DEST_RAY)/src/gui/
	
# 	$(LINK) $(DEST_RAY)/src/bin/ray-jack_checker_daemon $(DESTDIR)$(PREFIX)/bin/
# 	$(LINK) $(DEST_RAY)/src/bin/ray-jack_config_script  $(DESTDIR)$(PREFIX)/bin/
# 	$(LINK) $(DEST_RAY)/src/bin/ray-pulse2jack          $(DESTDIR)$(PREFIX)/bin/
# 	$(LINK) $(DEST_RAY)/src/bin/ray_git                 $(DESTDIR)$(PREFIX)/bin/
	
# 	# compile python files
# 	$(PYTHON) -m compileall $(DEST_RAY)/src/
	
# 	# install local manual
# 	cp -r manual $(DEST_RAY)/
	
# 	# install utility-scripts
# 	cp -r utility-scripts $(DEST_RAY)/
	
# 	# install main bash scripts to bin
# 	install -m 755 data/raysession  $(DESTDIR)$(PREFIX)/bin/
# 	install -m 755 data/ray-daemon  $(DESTDIR)$(PREFIX)/bin/
# 	install -m 755 data/ray_control $(DESTDIR)$(PREFIX)/bin/
# 	install -m 755 data/ray-proxy   $(DESTDIR)$(PREFIX)/bin/
	
# 	# modify PREFIX in main bash scripts
# 	sed -i "s?X-PREFIX-X?$(PREFIX)?" \
# 		$(DESTDIR)$(PREFIX)/bin/raysession \
# 		$(DESTDIR)$(PREFIX)/bin/ray-daemon \
# 		$(DESTDIR)$(PREFIX)/bin/ray_control \
# 		$(DESTDIR)$(PREFIX)/bin/ray-proxy
	
# 	# Install Translations
# 	install -m 644 locale/*.qm $(DEST_RAY)/locale/

# uninstall:
# 	rm -f $(DESTDIR)$(PREFIX)/bin/raysession
# 	rm -f $(DESTDIR)$(PREFIX)/bin/ray-daemon
# 	rm -f $(DESTDIR)$(PREFIX)/bin/ray-proxy
# 	rm -f $(DESTDIR)$(PREFIX)/bin/ray-jack_checker_daemon
# 	rm -f $(DESTDIR)$(PREFIX)/bin/ray-jack_config_script
# 	rm -f $(DESTDIR)$(PREFIX)/bin/ray-pulse2jack
# 	rm -f $(DESTDIR)$(PREFIX)/bin/ray_control
# 	rm -f $(DESTDIR)$(PREFIX)/bin/ray_git
	
# 	rm -f $(DESTDIR)$(PREFIX)/share/applications/raysession.desktop
# 	rm -f $(DESTDIR)$(PREFIX)/share/icons/hicolor/*/apps/raysession.png
# 	rm -f $(DESTDIR)$(PREFIX)/share/icons/hicolor/scalable/apps/raysession.svg
# 	rm -rf $(DESTDIR)/etc/xdg/raysession/client_templates/40_ray_nsm
# 	rm -rf $(DESTDIR)/etc/xdg/raysession/client_templates/60_ray_lash
# 	rm -rf $(DEST_RAY)
