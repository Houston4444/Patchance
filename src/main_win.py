
from dis import dis
from re import L
from typing import TYPE_CHECKING
from PyQt5.QtWidgets import QMainWindow, QShortcut, QMenu, QApplication, QToolButton
from PyQt5.QtCore import Qt

from about_dialog import AboutDialog
from patchbay.tools_widgets import PatchbayToolsWidget
from patchbay.base_elements import ToolDisplayed

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
        self.last_separator = self.main_menu.addSeparator()
        self.main_menu.addMenu(self.ui.menuHelp)
        self.main_menu.addAction(self.ui.actionShowMenuBar)
        self.main_menu.addAction(self.ui.actionQuit)
        
        self.menu_button = self.ui.toolBar.widgetForAction(self.ui.actionMainMenu)
        if TYPE_CHECKING:
            assert isinstance(self.menu_button, QToolButton)
        self.menu_button.setPopupMode(QToolButton.InstantPopup)
        self.menu_button.setMenu(self.main_menu)
        
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
        
        patchbay_tools_act = self.ui.toolBar.addWidget(PatchbayToolsWidget())
        self.patchbay_tools = self.ui.toolBar.widgetForAction(patchbay_tools_act)
        
        self.ui.graphicsView.setFocus()
        
    def finish_init(self, main: 'Main'):
        self.patchbay_manager = main.patchbay_manager
        self.settings = main.settings
        self.ui.toolBar.set_patchbay_manager(main.patchbay_manager)
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
        
        default_disp_widg = (
            ToolDisplayed.PORT_TYPES_VIEW
            | ToolDisplayed.ZOOM_SLIDER
            | ToolDisplayed.TRANSPORT_CLOCK
            | ToolDisplayed.TRANSPORT_PLAY_STOP
            | ToolDisplayed.BUFFER_SIZE
            | ToolDisplayed.SAMPLERATE
            | ToolDisplayed.XRUNS
            | ToolDisplayed.DSP_LOAD)
        
        default_disp_str = self.settings.value('tool_bar/elements', '', type=str)

        self.ui.toolBar.set_default_displayed_widgets(
            default_disp_widg.filtered_by_string(default_disp_str))

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
            self.ui.toolBar.setVisible(True)
            self.showNormal()
            if self._normal_screen_maximized:
                self.showMaximized()
            
            self.ui.menubar.setVisible(self._normal_screen_had_menu)
                
        else:
            self._normal_screen_maximized = self.isMaximized()
            self._normal_screen_had_menu = self.ui.menubar.isVisible()
            self.ui.menubar.setVisible(False)
            self.ui.toolBar.setVisible(False)
            self.ui.verticalLayout.setContentsMargins(0, 0, 0, 0)
            self.showFullScreen()

    def toggle_filter_frame_visibility(self):
        self.ui.filterFrame.setVisible(
            not self.ui.filterFrame.isVisible())
        
    def closeEvent(self, event):
        self.settings.setValue('MainWindow/geometry', self.saveGeometry())
        self.settings.setValue(
            'tool_bar/elements',
            self.ui.toolBar.get_displayed_widgets().to_save_string())
    
        super().closeEvent(event)
    