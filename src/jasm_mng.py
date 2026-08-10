
'''
This module manages the communication with JASM server,
a NSM server. The communication uses OSC protocol, it allows
to identify some JACK groups as NSM clients, and hide/show their
optional GUI from the patchbay.

See https://codeberg.org/jasm
'''

import logging
import os
import threading
from typing import TYPE_CHECKING

from osclib import Server


if TYPE_CHECKING:
    from patchance_pb_manager import PatchancePatchbayManager

_logger = logging.getLogger(__name__)

JASM_URL = os.getenv('jasm_url', 'osc.udp://localhost:62010')


def group_belongs_to_client(group_name: str, jack_client_name: str) -> bool:
    if group_name == jack_client_name:
        return True

    if group_name.startswith(jack_client_name + '/'):
        return True

    if (group_name.startswith(jack_client_name + ' (')
            and group_name.endswith(')')):
        # Non-Mixer way
        return True

    if group_name == jack_client_name + '-midi':
        # Hydrogen specific
        return True

    return False


class NsmClient:
    executable = ''
    name = ''
    has_optional_gui = False
    gui_visible = False
    icon = ''


class NsmClients(dict[str, NsmClient]):
    def client_for_jack_group(
            self, group_name: str) -> tuple[str, NsmClient] | None:
        for client_id, nsm_client in self.items():
            if group_belongs_to_client(
                    group_name, f'{nsm_client.name}.{client_id}'):
                return client_id, nsm_client

nsm_clients = NsmClients()
    

class JasmServer(Server):
    def __init__(self, patchbay_mng: 'PatchancePatchbayManager'):
        super().__init__()
        self._patchbay_mng = patchbay_mng
        self.add_method(None, None, self._receive)
        
        self._running = False
        self._thread = threading.Thread(target=self._run)
    
    def _run(self):
        while self._running:
            self.recv(50)

    def start(self):
        self.send(JASM_URL, '/jasm/gui/subscribe', ':clients:', 1)
        self._running = True
        self._thread.start()
    
    def stop(self):
        self._running = False
        self._thread.join()
        self.send(JASM_URL, '/jasm/gui/unsubscribe', ':clients:', 0)
    
    def _receive(self, path: str, args: list, types: str, src_addr):
        _logger.info(f'OSC received: {path} {args}')
        
        match (path, types):
            case ('/nsm/gui/client/new', 'ss'):
                id_info: tuple[str, str] = args # type:ignore
                client_id, client_info = id_info

                nsm_client = nsm_clients.get(client_id)
                if nsm_client is None:
                    nsm_client = NsmClient()
                    nsm_client.executable = client_info
                    nsm_clients[client_id] = nsm_client
                else:
                    nsm_client.name = client_info
            
            case ('/nsm/gui/client/has_optional_gui', 's'):
                client_id: str = args[0] # type:ignore
                nsm_client = nsm_clients.get(client_id)
                if nsm_client is None:
                    _logger.warning(
                        f'receive {path} for unknown client: {client_id}')
                    return

                nsm_client.has_optional_gui = True
                
            case ('/nsm/gui/client/gui_visible', 'si'):
                id_vis: tuple[str, int] = args # type:ignore
                client_id, gui_visible = id_vis
                nsm_client = nsm_clients.get(client_id)
                if nsm_client is None:
                    _logger.warning(
                        f'receive {path} for unknown client: {client_id}')
                    return
                
                nsm_client.gui_visible = bool(gui_visible)
                self._patchbay_mng.nsm_gui_visibility_changed(client_id)
            
            case ('/nsm/gui/client/status', 'ss'):
                id_status: tuple[str, str] = args # type:ignore
                client_id, status = id_status
                if status == 'removed':
                    if client_id in nsm_clients:
                        nsm_clients.pop(client_id)
                        
            case ('/nsm/gui/client/switch', 'ss'):
                old_new: tuple[str, str] = args # type:ignore
                old_id, new_id = old_new
                nsm_clients[new_id] = nsm_clients.pop(old_id)
        
    def set_gui_state(self, client_id: str, gui_state: bool):
        if gui_state:
            self.send(
                JASM_URL, '/nsm/gui/client/show_optional_gui', client_id)
        else:
            self.send(
                JASM_URL, '/nsm/gui/client/hide_optional_gui', client_id)

