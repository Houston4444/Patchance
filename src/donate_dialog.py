from qtpy.QtCore import QUrl
from qtpy.QtGui import QDesktopServices, QIcon
from qtpy.QtWidgets import QDialog

from patchbay.tools_widgets import is_dark_theme

from ui.donations import Ui_Dialog


class DonationsDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        
        self.ui.checkBox.setVisible(False)
        
        dark = '-dark' if is_dark_theme(self) else ''
        self.ui.toolButtonImage.setIcon(
            QIcon(f':scalable/breeze{dark}/handshake-deal.svg'))
        
        self.ui.toolButtonDonate.clicked.connect(self._donate)
        
    def _donate(self):
        QDesktopServices.openUrl(
            QUrl('https://liberapay.com/Houston4444'))