
'''
This module manages the communication with JASM server,
a NSM server. The communication uses OSC protocol, it allows
to identify some JACK groups as NSM clients, and hide/show their
optional GUI from the patchbay.

See https://codeberg.org/jasm
'''

import logging
import os
from typing import TYPE_CHECKING

from .nsm_client import nsm_clients

if TYPE_CHECKING:
    from patchance_pb_manager import PatchancePatchbayManager

_logger = logging.getLogger(__name__)


class JasmServer:
    def __init__(
            self, jasm_url: str, pb_manager: 'PatchancePatchbayManager'):
        self._patchbay_mng = pb_manager
        self._osc_running = False
        self._osc_server = None

        if not jasm_url:
            jasm_url = os.getenv('jasm_url', '')

        if not jasm_url:
            return
        
        try:
            from osclib import Address
        except:
            _logger.error(
                'liblo or pyliblo3 for python is missing. '
                'Impossible to communicate with JASM')
            return

        try:
            jasm_addr = Address(jasm_url)
        except:
            _logger.error(
                f'Attempting to connect to JASM '
                f'with an invalid OSC url: {jasm_url}')
        else:
            from .osc_server import JasmOscServer
            self._osc_server = JasmOscServer(jasm_addr, pb_manager)
    
    def start(self):
        if self._osc_server is None:
            return

        self._osc_running = True
        self._osc_server.start()
    
    def stop(self):
        if self._osc_server is None or not self._osc_running:
            return

        self._osc_server.stop()
        self._osc_running = False
        
    def set_gui_state(self, client_id: str, gui_state: bool):
        if self._osc_server is None:
            _logger.warning(
                'Attempting to change optional-gui state without OSC server')
            return

        if gui_state:
            self._osc_server.to_jasm(
                '/nsm/gui/client/show_optional_gui', client_id)
        else:
            self._osc_server.to_jasm(
                '/nsm/gui/client/hide_optional_gui', client_id)