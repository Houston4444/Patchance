
from typing import TYPE_CHECKING
from PyQt5.QtWidgets import QApplication, QMainWindow, QShortcut
from PyQt5.QtCore import Qt

from .ui.main_win import Ui_MainWindow
from .patchbay.patchcanvas.scene import PatchScene

if TYPE_CHECKING:
    from patchance import Main


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.patchbay_manager = None
        self.settings = None

        self.ui.filterFrame.setVisible(False)

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

        self.scene = PatchScene(self, self.ui.graphicsView)
        self.ui.graphicsView.setScene(self.scene)
        # self.setWindowFlag(Qt.FramelessWindowHint, True)
        
        self._normal_screen_maximized = False
        
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
                
        else:
            self._normal_screen_maximized = self.isMaximized()
            self.ui.topWidget.setVisible(False)
            self.ui.verticalLayout.setContentsMargins(0, 0, 0, 0)
            self.showFullScreen()

    def toggle_filter_frame_visibility(self):
        self.ui.filterFrame.setVisible(
            not self.ui.filterFrame.isVisible())
        
    def closeEvent(self, event):
        self.settings.setValue('MainWindow/geometry', self.saveGeometry())
        if self.patchbay_manager is not None:
            self.patchbay_manager.save_positions()
        super().closeEvent(event)
    