
import typing
from PyQt5.QtWidgets import QMainWindow

from .ui.main_win import Ui_MainWindow
from .patchbay.patchcanvas.scene import PatchScene


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.scene = PatchScene(self, self.ui.graphicsView)
        self.ui.graphicsView.setScene(self.scene)