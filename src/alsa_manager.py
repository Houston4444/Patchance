
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from threading import Thread

    
from pyalsa import alsaseq
from pyalsa.alsaseq import (
    SEQ_USER_CLIENT,
    SEQ_PORT_CAP_NO_EXPORT,
    SEQ_PORT_CAP_READ,
    SEQ_PORT_CAP_SUBS_READ,
    SEQ_PORT_CAP_WRITE,
    SEQ_PORT_CAP_SUBS_WRITE,
    SEQ_PORT_TYPE_APPLICATION,
    SEQ_CLIENT_SYSTEM,
    SEQ_PORT_SYSTEM_ANNOUNCE,
    SEQ_EVENT_CLIENT_START,
    SEQ_EVENT_CLIENT_EXIT,
    SEQ_EVENT_PORT_START,
    SEQ_EVENT_PORT_EXIT,
    SEQ_EVENT_PORT_SUBSCRIBED,
    SEQ_EVENT_PORT_UNSUBSCRIBED,
    SequencerError
)
from patchbay.base_elements import JackPortFlag, PortType

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


@dataclass
class AlsaConn:
    source_client_id: int
    source_port_id: int
    dest_client_id: int
    dest_port_id: int


class AlsaClient:
    def __init__(self, alsa_mng: 'AlsaManager', name: str, id: int):
        self.alsa_mng = alsa_mng
        self.name = name
        self.id = id
        self.ports = dict[int, AlsaPort]()
            
    def __repr__(self) -> str:
        return f"AlsaClient({self.name}, {self.id})"
    
    def add_port(self, port_id: int):
        port_info = self.alsa_mng.seq.get_port_info(port_id, self.id)
        caps = port_info['capability']
        if caps & SEQ_PORT_CAP_NO_EXPORT:
            return
        
        if not(caps & _PORT_READS == _PORT_READS
               or caps & _PORT_WRITES == _PORT_WRITES):
            return

        physical = not bool(port_info['type'] & SEQ_PORT_TYPE_APPLICATION)
        self.ports[port_id] = AlsaPort(port_info['name'], port_id, caps, physical)


class AlsaManager:
    def __init__(self, patchbay_manager: 'PatchbayManager'):
        self._patchbay_manager = patchbay_manager
        self.seq = alsaseq.Sequencer(clientname='patchance')

        self._all_alsa_connections = list[AlsaConn]()
        self._connections = list[AlsaConn]()
        self._clients = dict[int, AlsaClient]()
        self._clients_names = dict[int, str]()
        
        self._stopping = False
        self._event_thread = Thread(target=self.read_events)

        port_caps = (SEQ_PORT_CAP_WRITE
                     | SEQ_PORT_CAP_SUBS_WRITE
                     | SEQ_PORT_CAP_NO_EXPORT)
        input_id = self.seq.create_simple_port(
            name="patchance_port",
            type=SEQ_PORT_TYPE_APPLICATION,
            caps=port_caps)

        self.seq.connect_ports(
            (SEQ_CLIENT_SYSTEM, SEQ_PORT_SYSTEM_ANNOUNCE),
            (self.seq.client_id, input_id))

    def get_the_graph(self):
        if self.seq is None:
            return
        
        clients = self.seq.connection_list()
        
        self._clients_names.clear()
        self._clients.clear()
        self._all_alsa_connections.clear()

        for client in clients:
            client_name, client_id, port_list = client
            self._clients_names[client_id] = client_name
            self._clients[client_id] = AlsaClient(
                self, client_name, client_id)
            for port_name, port_id, connection_list in port_list:
                self._clients[client_id].add_port(port_id)
      
                connections = connection_list[0]
                for connection in connections:
                    conn_client_id, conn_port_id = connection[:2]                    
                    self._all_alsa_connections.append(
                        AlsaConn(client_id, port_id,
                                 conn_client_id, conn_port_id))

    def add_port_to_patchbay(self, client: AlsaClient, port: AlsaPort):
        port_flags = 0
        if port.physical:
            port_flags = JackPortFlag.IS_PHYSICAL
        
        if port.caps & _PORT_READS == _PORT_READS:
            self._patchbay_manager.add_port(
                f'ALSA_OUT:{client.name}:{port.name}',
                PortType.MIDI_ALSA,
                port_flags | JackPortFlag.IS_OUTPUT,
                client.id * 0x10000 + port.id)
        if port.caps & _PORT_WRITES == _PORT_WRITES:
            self._patchbay_manager.add_port(
                f'ALSA_IN:{client.name}:{port.name}',
                PortType.MIDI_ALSA,
                port_flags | JackPortFlag.IS_INPUT,
                client.id * 0x10000 + port.id)

    def remove_port_from_patchbay(self, client: AlsaClient, port: AlsaPort):
        if port.caps & _PORT_READS == _PORT_READS:
            self._patchbay_manager.remove_port(
                f"ALSA_OUT:{client.name}:{port.name}")
        if port.caps & _PORT_WRITES == _PORT_WRITES:
            self._patchbay_manager.remove_port(
                f"ALSA_IN:{client.name}:{port.name}")

    def add_all_ports(self):
        self.get_the_graph()

        for client in self._clients.values():
            if client.name == 'System':
                continue

            for port in client.ports.values():
                self.add_port_to_patchbay(client, port)
                
        for conn in self._all_alsa_connections:
            source_client = self._clients.get(conn.source_client_id)
            dest_client = self._clients.get(conn.dest_client_id)
            if source_client is None or dest_client is None:
                continue
            
            source_port = source_client.ports.get(conn.source_port_id)
            dest_port = dest_client.ports.get(conn.dest_port_id)
            
            if source_port is None or dest_port is None:
                continue
            
            self._connections.append(conn)
            
            self._patchbay_manager.add_connection(
                f"ALSA_OUT:{source_client.name}:{source_port.name}",
                f"ALSA_IN:{dest_client.name}:{dest_port.name}")

        self._event_thread.start()
    
    def connect_ports(self, port_out_name: str, port_in_name: str,
                      disconnect=False):
        alsa_key, src_client_name, *rest = port_out_name.split(':')
        src_port_name = ':'.join(rest)
        alsa_key, dest_client_name, *rest = port_in_name.split(':')
        dest_port_name = ':'.join(rest)
        
        port_out_name = port_out_name.replace('ALSA_OUT:', '', 1)
        port_in_name = port_in_name.replace('ALSA_IN:', '', 1)

        for src_client_id, src_client in self._clients.items():
            if src_client.name == src_client_name:
                break
        else:
            return
        
        for src_port_id, src_port in src_client.ports.items():
            if src_port.name == src_port_name:
                break
        else:
            return
        
        for dest_client_id, dest_client in self._clients.items():
            if dest_client.name == dest_client_name:
                break
        else:
            return
        
        for dest_port_id, dest_port in dest_client.ports.items():
            if dest_port.name == dest_port_name:
                break
        else:
            return
        
        if disconnect:
            self.seq.disconnect_ports(
                (src_client_id, src_port_id),
                (dest_client_id, dest_port_id))
        else: 
            self.seq.connect_ports(
                (src_client_id, src_port_id),
                (dest_client_id, dest_port_id),
                0, 0, 0, 0)
        
    def read_events(self):
        while True:
            if self._stopping:
                break

            event_list = self.seq.receive_events(timeout=128, maxevents=1)

            for event in event_list:
                data = event.get_data()

                if event.type == SEQ_EVENT_CLIENT_START:
                    client_id = data['addr.client']
                    client_info = self.seq.get_client_info(client_id)
                    self._clients[client_id] = AlsaClient(
                        self, client_info['name'], client_id)
                elif event.type == SEQ_EVENT_CLIENT_EXIT:
                    client_id = data['addr.client']
                    client = self._clients[client_id]
                    if client is not None:
                        for port in client.ports.values():
                            self.remove_port_from_patchbay(client, port)

                    del self._clients[client_id]
                    
                elif event.type == SEQ_EVENT_PORT_START:
                    client_id, port_id = data['addr.client'], data['addr.port']
                    client = self._clients.get(client_id)
                    if client is None:
                        continue
                    
                    client.add_port(port_id)
                    port = client.ports.get(port_id)
                    if port is None:
                        continue
                    
                    self.add_port_to_patchbay(client, port)
                    
                elif event.type == SEQ_EVENT_PORT_EXIT:
                    client_id, port_id = data['addr.client'], data['addr.port']
                    client = self._clients.get(client_id)
                    if client is None:
                        continue

                    port = client.ports.get(port_id)
                    if port is None:
                        continue
                    
                    self.remove_port_from_patchbay(client, port)
                    
                elif event.type == SEQ_EVENT_PORT_SUBSCRIBED:
                    sender_client = self._clients.get(data['connect.sender.client'])
                    dest_client = self._clients.get(data['connect.dest.client'])
                    if sender_client is None or dest_client is None:
                        continue
                    
                    sender_port = sender_client.ports.get(data['connect.sender.port'])
                    dest_port = dest_client.ports.get(data['connect.dest.port'])
                    
                    if sender_port is None or dest_port is None:
                        continue

                    self._connections.append(
                        AlsaConn(sender_client.id, sender_port.id,
                                 dest_client.id, dest_port.id))

                    self._patchbay_manager.add_connection(
                        f"ALSA_OUT:{sender_client.name}:{sender_port.name}",
                        f"ALSA_IN:{dest_client.name}:{dest_port.name}")
                    
                elif event.type == SEQ_EVENT_PORT_UNSUBSCRIBED:
                    sender_client = self._clients.get(data['connect.sender.client'])
                    dest_client = self._clients.get(data['connect.dest.client'])
                    if sender_client is None or dest_client is None:
                        continue
                    
                    sender_port = sender_client.ports.get(data['connect.sender.port'])
                    dest_port = dest_client.ports.get(data['connect.dest.port'])
                    
                    if sender_port is None or dest_port is None:
                        continue
                    
                    for conn in self._connections:
                        if (conn.source_client_id == sender_client.id
                                and conn.source_port_id == sender_port.id
                                and conn.dest_client_id == dest_client.id
                                and conn.dest_port_id == dest_port.id):
                            self._connections.remove(conn)
                            break 

                    self._patchbay_manager.remove_connection(
                        f"ALSA_OUT:{sender_client.name}:{sender_port.name}",
                        f"ALSA_IN:{dest_client.name}:{dest_port.name}")
                
    def stop_events_loop(self):
        self._stopping = True
        
        self._event_thread.join()
        
        for client in self._clients.values():
            for port in client.ports.values():
                self.remove_port_from_patchbay(client, port)
        
        del self._event_thread
        self._event_thread = Thread(target=self.read_events)
    
    