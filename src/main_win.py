
from typing import TYPE_CHECKING

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QResizeEvent, QKeyEvent
from PyQt5.QtWidgets import (
    QMainWindow, QShortcut, QMenu, QApplication, QToolButton)

from about_dialog import AboutDialog
from patchbay.tools_widgets import PatchbayToolsWidget, TextWithIcons
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
        
        self.menu_button: QToolButton = self.ui.toolBar.widgetForAction(
            self.ui.actionMainMenu)
        self.menu_button.setPopupMode(QToolButton.InstantPopup)
        self.menu_button.setMenu(self.main_menu)
        
        self.ui.filterFrame.setVisible(False)
        self.ui.actionShowMenuBar.toggled.connect(self._menubar_shown_toggled)
        self.ui.actionQuit.triggered.connect(QApplication.quit)
        self.ui.actionAboutPatchance.triggered.connect(
            self._show_about_dialog)
        self.ui.actionAboutQt.triggered.connect(QApplication.aboutQt)

        # prevent toolbar hideability
        self.ui.toolBar.toggleViewAction().setEnabled(False)
        self.ui.toolBar.toggleViewAction().setVisible(False)

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
        
        self.patchbay_tools = PatchbayToolsWidget()
        self.patchbay_tools._text_with_icons = TextWithIcons.NO
        self.patchbay_tools.no_text_with_icons_act = True
        self.patchbay_tools.set_tool_bars(
            self.ui.toolBar, self.ui.toolBarTransport,
            self.ui.toolBarJack, self.ui.toolBarCanvas)

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
        
        default_disp_widg = (
            ToolDisplayed.HIDDENS_BOX
            | ToolDisplayed.PORT_TYPES_VIEW
            | ToolDisplayed.ZOOM_SLIDER
            | ToolDisplayed.TRANSPORT_CLOCK
            | ToolDisplayed.TRANSPORT_PLAY_STOP
            | ToolDisplayed.BUFFER_SIZE
            | ToolDisplayed.SAMPLERATE
            | ToolDisplayed.XRUNS
            | ToolDisplayed.DSP_LOAD)
        
        default_disp_str = self.settings.value(
            'tool_bar/elements', '', type=str)

        self.patchbay_tools.change_tools_displayed(
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

            for toolbar in (self.ui.toolBar, self.ui.toolBarTransport,
                            self.ui.toolBarJack, self.ui.toolBarCanvas):
                toolbar.setVisible(True)

            self.showNormal()
            if self._normal_screen_maximized:
                self.showMaximized()
            
            self.ui.menubar.setVisible(self._normal_screen_had_menu)
                
        else:
            self._normal_screen_maximized = self.isMaximized()
            self._normal_screen_had_menu = self.ui.menubar.isVisible()
            self.ui.menubar.setVisible(False)

            for toolbar in (self.ui.toolBar, self.ui.toolBarTransport,
                            self.ui.toolBarJack, self.ui.toolBarCanvas):
                toolbar.setVisible(False)
            
            self.ui.verticalLayout.setContentsMargins(0, 0, 0, 0)
            self.showFullScreen()

    def toggle_filter_frame_visibility(self):
        self.ui.filterFrame.setVisible(
            not self.ui.filterFrame.isVisible())
        
    def closeEvent(self, event):
        self.settings.setValue('MainWindow/geometry', self.saveGeometry())
        self.settings.setValue(
            'tool_bar/elements',
            self.patchbay_tools._tools_displayed.to_save_string())
    
        super().closeEvent(event)
        
    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self.patchbay_tools.main_win_resize(self)
        
    def keyPressEvent(self, event: QKeyEvent):
        super().keyPressEvent(event)
        if self.patchbay_manager is not None:
            self.patchbay_manager.key_press_event(event)
    