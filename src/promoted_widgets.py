

from patchbay import (PatchbayToolsWidget, FilterFrame, PatchGraphicsView,
                      TransportControlsFrame)


class JackStatesWidget(PatchbayToolsWidget):
    def __init__(self, parent):
        super().__init__()
        

class PatchFilterFrame(FilterFrame):
    pass
        
class PatchanceGraphicsView(PatchGraphicsView):
    pass

class PatchanceTransportControls(TransportControlsFrame):
    pass