
from qtpy.QtWidgets import QDialog, QApplication
from qtpy.QtCore import QSize

import resourcer

from ui.about_patchance import Ui_DialogAboutPatchance

class AboutDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.ui = Ui_DialogAboutPatchance()
        self.ui.setupUi(self)
        self.ui.labelPixmap.setPixmap(
            resourcer.main_icon().pixmap(QSize(128, 128)))
        self.ui.labelRayAndVersion.setText(
            self.ui.labelRayAndVersion.text() % QApplication.applicationVersion())