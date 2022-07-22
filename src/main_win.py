
from typing import TYPE_CHECKING
from PyQt5.QtWidgets import QMainWindow, QShortcut
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

        self.ui.filterFrame.setVisible(False)

        filter_bar_shortcut = QShortcut('Ctrl+F', self)
        filter_bar_shortcut.setContext(Qt.ApplicationShortcut)
        filter_bar_shortcut.activated.connect(
            self.toggle_filter_frame_visibility)

        self.scene = PatchScene(self, self.ui.graphicsView)
        self.ui.graphicsView.setScene(self.scene)
        
    def finish_init(self, main: 'Main'):
        self.ui.filterFrame.set_patchbay_manager(main.patchbay_manager)
        main.patchbay_manager.sg.filters_bar_toggle_wanted.connect(
            self.toggle_filter_frame_visibility)
        
    def toggle_filter_frame_visibility(self):
        self.ui.filterFrame.setVisible(
            not self.ui.filterFrame.isVisible())