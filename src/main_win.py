
from tkinter import dialog
from typing import TYPE_CHECKING
from PyQt5.QtWidgets import QMainWindow, QShortcut, QMenu, QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from about_dialog import AboutDialog

from ui.main_win import Ui_MainWindow


if TYPE_CHECKING:
    from patchance import Main


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.patchbay_manager = None
        self.settings = None

        self.main_menu = QMenu()
        self.main_menu.addAction(self.ui.actionShowMenuBar)
        self.last_separator = self.main_menu.addSeparator()
        self.main_menu.addMenu(self.ui.menuHelp)
        self.main_menu.addAction(self.ui.actionQuit)
        self.ui.toolButton.setMenu(self.main_menu)

        self.ui.filterFrame.setVisible(False)
        self.ui.actionShowMenuBar.toggled.connect(self._menubar_shown_toggled)
        self.ui.actionQuit.triggered.connect(QApplication.quit)
        self.ui.actionAboutPatchance.triggered.connect(self._show_about_dialog)
        self.ui.actionAboutQt.triggered.connect(QApplication.aboutQt)

        filter_bar_shortcut = QShortcut('Ctrl+F', self)
        filter_bar_shortcut.setContext(Qt.ApplicationShortcut)
        filter_bar_shortcut.activated.connect(
            self.toggle_filter_frame_visibility)
        
        refresh_shortcut = QShortcut('Ctrl+R', self)
        refresh_shortcut.setContext(Qt.ApplicationShortcut)
        refresh_shortcut.activated.connect(self.refresh_patchbay)
        refresh_shortcut_alt = QShortcut('F5', self)
        refresh_shortcut_alt.setContext(Qt.ApplicationShortcut)
        refresh_shortcut_alt.activated.connect(self.refresh_patchbay)
        
        self._normal_screen_maximized = False
        self._normal_screen_had_menu = False
        
        self.ui.graphicsView.setFocus()
        
    def finish_init(self, main: 'Main'):
        self.patchbay_manager = main.patchbay_manager
        self.settings = main.settings
        self.ui.filterFrame.set_patchbay_manager(main.patchbay_manager)
        main.patchbay_manager.sg.filters_bar_toggle_wanted.connect(
            self.toggle_filter_frame_visibility)
        main.patchbay_manager.sg.full_screen_toggle_wanted.connect(
            self.toggle_patchbay_full_screen)
        geom = self.settings.value('MainWindow/geometry')

        if geom:
            self.restoreGeometry(geom)
            
        self._normal_screen_maximized = self.isMaximized()
        
        show_menubar = self.settings.value(
            'MainWindow/show_menubar', False, type=bool)
        self.ui.actionShowMenuBar.setChecked(show_menubar)
        self.ui.menubar.setVisible(show_menubar)

        self.ui.menubar.addMenu(main.patchbay_manager.canvas_menu)
        self.main_menu.insertMenu(
            self.last_separator, main.patchbay_manager.canvas_menu)

    def _menubar_shown_toggled(self, state: int):
        self.ui.menubar.setVisible(bool(state))
    
    def _show_about_dialog(self):
        dialog = AboutDialog(self)
        dialog.exec()
    
    def refresh_patchbay(self):
        if self.patchbay_manager is None:
            return
        
        self.patchbay_manager.refresh()
    
    def toggle_patchbay_full_screen(self):
        if self.isFullScreen():
            self.ui.verticalLayout.setContentsMargins(2, 2, 2, 2)
            self.ui.topWidget.setVisible(True)
            self.showNormal()
            if self._normal_screen_maximized:
                self.showMaximized()
            
            self.ui.menubar.setVisible(self._normal_screen_had_menu)
                
        else:
            self._normal_screen_maximized = self.isMaximized()
            self._normal_screen_had_menu = self.ui.menubar.isVisible()
            self.ui.menubar.setVisible(False)
            self.ui.topWidget.setVisible(False)
            self.ui.verticalLayout.setContentsMargins(0, 0, 0, 0)
            self.showFullScreen()

    def toggle_filter_frame_visibility(self):
        self.ui.filterFrame.setVisible(
            not self.ui.filterFrame.isVisible())
        
    def closeEvent(self, event):
        self.settings.setValue('MainWindow/geometry', self.saveGeometry())
        super().closeEvent(event)
    