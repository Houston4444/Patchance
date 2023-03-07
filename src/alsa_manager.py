
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from patchbay.base_elements import JackPortFlag, PortType
    
from pyalsa import alsaseq
from pyalsa.alsaseq import (
    SEQ_USER_CLIENT,
    SEQ_PORT_CAP_NO_EXPORT,
    SEQ_PORT_CAP_READ,
    SEQ_PORT_CAP_SUBS_READ,
    SEQ_PORT_CAP_WRITE,
    SEQ_PORT_CAP_SUBS_WRITE,
    SEQ_PORT_TYPE_APPLICATION
)

if TYPE_CHECKING:
    from patchbay.patchbay_manager import PatchbayManager


_PORT_READS = SEQ_PORT_CAP_READ | SEQ_PORT_CAP_SUBS_READ
_PORT_WRITES = SEQ_PORT_CAP_WRITE | SEQ_PORT_CAP_SUBS_WRITE

@dataclass
class AlsaPort:
    name: str
    id: int
    caps: int
    physical: bool


class AlsaClient:
    def __init__(self, alsa_mng: 'AlsaManager', name: str, id: int,
                 physical: bool,
                 ports: list[tuple[str, int, Any]]):
        self.alsa_mng = alsa_mng
        self.name = name
        self.id = id
        self.ports = dict[str, AlsaPort]()
        
        for port in ports:
            port_name, port_id, connection_list = port
            port_info = self.alsa_mng.seq.get_port_info(port_id, id)
            caps = port_info['capability']
            if caps & SEQ_PORT_CAP_NO_EXPORT:
                continue
            
            if not(caps & _PORT_READS == _PORT_READS
                    or caps & _PORT_WRITES == _PORT_WRITES):
                continue

            physical = not bool(port_info['type'] & SEQ_PORT_TYPE_APPLICATION)
            # print(port_name, port_type & SEQ_PORT_TYPE_APPLICATION)
            port_name, port_id, connection_list = port
            self.ports[port_name] = AlsaPort(port_name, port_id, caps, physical)
            
    def __repr__(self) -> str:
        return f"AlsaClient({self.name}, {self.id})"


class AlsaManager:
    def __init__(self, patchbay_manager: 'PatchbayManager'):
        self._patchbay_manager = patchbay_manager
        self.seq = alsaseq.Sequencer(clientname='patchance')

        # port_caps = SND_SEQ_PORT_CAP_WRITE |SND_SEQ_PORT_CAP_SUBS_WRITE | SND_SEQ_PORT_CAP_NO_EXPORT
        port_caps = SEQ_PORT_CAP_WRITE |SEQ_PORT_CAP_SUBS_WRITE | SEQ_PORT_CAP_NO_EXPORT
        self.seq.create_simple_port(name="polpolpo", type=SEQ_PORT_TYPE_APPLICATION, caps=port_caps)

        self._active_connections = []
        self._clients = dict[str, AlsaClient]()
        self._clients_names = {}
    
    def get_client(self, name):
        if name in self._clients.keys():
            return self._clients[name]
        # TODO some log
    
    def get_port(self, client: AlsaClient, port_name: str) -> AlsaPort:
        if port_name in client.ports:
            return client.ports[port_name]
        else:
            # TODO some log
            pass

    def get_the_graph(self):
        if self.seq is None:
            return
        
        clients = self.seq.connection_list()
        
        self._clients_names.clear()
        self._clients.clear()
        self._active_connections.clear()

        for client in clients:
            client_name, client_id, port_list = client
            self._clients_names[client_id] = client_name
            self._clients[client_name] = AlsaClient(
                self, client_name, client_id, False, port_list)
      
            for port in port_list:
                port_name, port_id, connection_list = port
                port_info = self.seq.get_port_info(port_id, client_id)
                caps = port_info['capability']
                if caps & SEQ_PORT_CAP_NO_EXPORT:
                    continue

                if not(caps & _PORT_READS == _PORT_READS
                       or caps & _PORT_WRITES == _PORT_WRITES):
                    continue

                connections = connection_list[0]
                for connection in connections:
                    self._active_connections.append(
                        (client_id, port_id, connection[0], connection[1]))

    def add_all_ports(self):
        if self.seq is None:
            print('ALSA Lib pas Ok')
            return

        self.get_the_graph()

        for client_name, client in self._clients.items():
            if client_name == 'System':
                continue

            for port_name, port in client.ports.items():
                port_flags = 0
                if port.physical:
                    port_flags = JackPortFlag.IS_PHYSICAL
                
                if port.caps & _PORT_READS == _PORT_READS:
                    self._patchbay_manager.add_port(
                        f'{client_name}:{port_name}',
                        PortType.MIDI_ALSA,
                        port_flags | JackPortFlag.IS_OUTPUT,
                        client.id * 0x10000 + port.id)
                if port.caps & _PORT_WRITES == _PORT_WRITES:
                    self._patchbay_manager.add_port(
                        f'{client_name}:{port_name}',
                        PortType.MIDI_ALSA,
                        port_flags | JackPortFlag.IS_INPUT,
                        client.id * 0x10000 + port.id)