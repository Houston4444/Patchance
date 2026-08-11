
import logging
import threading
import time
from typing import TYPE_CHECKING

from osclib import Address, Server

from .nsm_client import NsmClient, nsm_clients

if TYPE_CHECKING:
    from patchance_pb_manager import PatchancePatchbayManager

_logger = logging.getLogger(__name__)


class JasmOscServer(Server):
    def __init__(self, jasm_addr: Address,
                 patchbay_mng: 'PatchancePatchbayManager'):
        super().__init__()
        self._patchbay_mng = patchbay_mng
        self._jasm_addr = jasm_addr
        self.add_method(None, None, self._receive)
        
        self._running = False
        self._thread = threading.Thread(target=self._run)
        
        self._waiting_announce = False
        self._start_time = 0.0
    
    def to_jasm(self, path: str, *args):
        self.send(self._jasm_addr, path, *args)
    
    def _run(self):
        while self._running:
            self.recv(50)
            
            if (self._waiting_announce
                    and time.time() - self._start_time > 1.0):
                _logger.warning(
                    f'No answer from JASM port at {self._jasm_addr.url}')
                self._waiting_announce = False

    def start(self):
        self._waiting_announce = True
        self._start_time = time.time()
        self.to_jasm('/jasm/gui/subscribe', ':clients:', 1)
        self._running = True
        self._thread.start()
    
    def stop(self):
        self._running = False
        self._thread.join()
        self.to_jasm('/jasm/gui/unsubscribe', ':clients:', 0)
    
    def _receive(self, path: str, args: list, types: str, src_addr):
        _logger.info(f'OSC received: {path} {args}')
        
        match (path, types):
            case ('/jasm/subscribe/reply', 'ss'):
                self._waiting_announce = False
            
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