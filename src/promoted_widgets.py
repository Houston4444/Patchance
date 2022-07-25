

from .patchbay import PatchbayToolsWidget, FilterFrame
from .patchbay import PatchGraphicsView


class JackStatesWidget(PatchbayToolsWidget):
    def __init__(self, parent):
        super().__init__()
        

class PatchFilterFrame(FilterFrame):
    def __init__(self, parent):
        super().__init__(parent)