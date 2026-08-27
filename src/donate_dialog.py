from qtpy.QtCore import QUrl
from qtpy.QtGui import QDesktopServices
from qtpy.QtWidgets import QDialog

from patchbay.tools_widgets import is_dark_theme
from resources import scalables
import resourcer

from ui.donations import Ui_Dialog


class DonationsDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        
        self.ui.checkBox.setVisible(False)        
        self.ui.toolButtonImage.setIcon(
            resourcer.icon(
                scalables.misc.HANDSHAKE_DEAL, dark=is_dark_theme(self)))
        self.ui.toolButtonDonate.setIcon(
            resourcer.icon(
                scalables.misc.LIBERAPAY_LOGO_BLACK_ON_YELLOW))
        self.ui.toolButtonDonate.clicked.connect(self._donate)

    def _donate(self):
        QDesktopServices.openUrl(
            QUrl('https://liberapay.com/Houston4444'))