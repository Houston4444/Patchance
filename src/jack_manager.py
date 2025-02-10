from dataclasses import dataclass
import math
import os
import threading
import time
from typing import TYPE_CHECKING
import logging
from queue import Queue

from qtpy.QtCore import QTimer

import jack

from patshared import JackMetadata, Naming
from patchbay.base_elements import TransportPosition
from patshared.jack_metadata import JackMetadatas
if TYPE_CHECKING:
    from patchance_pb_manager import PatchancePatchbayManager


_logger = logging.getLogger()


PORT_TYPE_NULL = 0
PORT_TYPE_AUDIO = 1
PORT_TYPE_MIDI = 2


# Define a context manager to suppress stdout and stderr.
class suppress_stdout_stderr(object):
    '''
    A context manager for doing a "deep suppression" of stdout and stderr in 
    Python, i.e. will suppress all print, even if the print originates in a 
    compiled C/Fortran sub-function.
       This will not suppress raised exceptions, since exceptions are printed
    to stderr just before a script exits, and after the context manager has
    exited (at least, I think that is why it lets exceptions through).      

    '''
    def __init__(self):
        # Open a pair of null files
        self.null_fds =  [os.open(os.devnull,os.O_RDWR) for x in range(2)]
        # Save the actual stdout (1) and stderr (2) file descriptors.
        self.save_fds = [os.dup(1), os.dup(2)]

    def __enter__(self):
        # Assign the null pointers to stdout and stderr.
        os.dup2(self.null_fds[0],1)
        os.dup2(self.null_fds[1],2)

    def __exit__(self, *_):
        # Re-assign the real stdout/stderr back to (1) and (2)
        os.dup2(self.save_fds[0],1)
        os.dup2(self.save_fds[1],2)
        # Close all file descriptors
        for fd in self.null_fds + self.save_fds:
            os.close(fd)
        

@dataclass
class JackPort:
    name: str
    type: int
    flags: int
    uuid: int
    conns: list[str]


@dataclass
class Metadata:
    uuid: int
    key: str
    value: str


class JackManager:
    def __init__(self, patchbay_manager: 'PatchancePatchbayManager'):
        self.jack_running = False
        self.client = None
        self.patchbay_manager = patchbay_manager

        self._stopped_sent = False

        self._dsp_n = 0
        self._last_dsp_sent = 0
        self._max_dsp_since_last_send = 0

        self._dsp_timer = QTimer()
        self._dsp_timer.setInterval(200)
        self._dsp_timer.timeout.connect(self._check_dsp)

        self._jack_checker_timer = QTimer()
        self._jack_checker_timer.setInterval(500)
        self._jack_checker_timer.timeout.connect(self.start_jack_client)
        
        self._transport_timer = QTimer()
        self._transport_timer.setInterval(50)
        self._transport_timer.timeout.connect(self._check_transport)

        self._check_pretty_time = 0.0
        self._check_pretty_timer = QTimer()
        self._check_pretty_timer.setInterval(100)
        self._check_pretty_timer.timeout.connect(self._check_pretty_names)
        self._check_pretty_queue = Queue[tuple[bool, bool, str, float]]()
        
        self._last_transport_pos = None
        
        self._client_uuids_sent = dict[str, int]()

        self.start_jack_client()
    
    @property
    def writes_pretty_names(self) -> bool:
        '''True when this jack client should export internal pretty names
        to JACK metadatas.'''
        return bool(self.patchbay_manager.jack_export_naming
                    & Naming.INTERNAL_PRETTY)
    
    def init_the_graph(self):
        if not self.jack_running:
            return
        
        pretty_names = self.patchbay_manager.pretty_names
        client_names = set[str]()
        jack_ports = list[JackPort]()
        
        # add all ports to jack_ports
        for port in self.client.get_ports():
            port_uuid = port.uuid
            port_name = port.name

            port_type = PORT_TYPE_NULL
            if port.is_audio:
                port_type = PORT_TYPE_AUDIO
            elif port.is_midi:
                port_type = PORT_TYPE_MIDI
                
            client_names.add(port_name.partition(':')[0])

            flags = jack._lib.jack_port_flags(port._ptr)

            if port.is_input:
                jack_ports.append(
                    JackPort(port.name, port_type, flags, port_uuid, []))
                continue
            
            # this port is output, list its connections
            jack_ports.append(
                JackPort(
                    port.name, port_type, flags, port_uuid,
                    [p.name for p in self.client.get_all_connections(port)]))
        
        # add all ports to patchbay manager
        for p in jack_ports:
            self.patchbay_manager.add_port(p.name, p.type, p.flags, p.uuid)

        # add all connections to patchbay_manager       
        for p in jack_ports:
            for in_port_name in p.conns:
                self.patchbay_manager.add_connection(p.name, in_port_name)
        
        # associate group names and uuids in patchbay manager
        for client_name in client_names:
            try:
                client_uuid = self.client.get_uuid_for_client_name(client_name)
                assert client_uuid.isdigit()
            except:
                continue          
            
            self.patchbay_manager.set_group_uuid_from_name(
                client_name, int(client_uuid))
            
            self._client_uuids_sent[client_name] = int(client_uuid)

        all_metadatas = dict[int, dict[str, str]]()
        jack_metadatas = JackMetadatas()

        for uuid, uuid_dict in jack.get_all_properties().items():
            all_metadatas[uuid] = dict[str, str]()

            for key, value_type in uuid_dict.items():
                value = value_type[0].decode()
                all_metadatas[uuid][key] = value
                jack_metadatas.add(uuid, key, value)
                self.patchbay_manager.metadata_update(uuid, key, value)

        if self.writes_pretty_names:
            for client_name in client_names:
                uuid = self._client_uuids_sent.get(client_name)
                if uuid is None:
                    continue
                
                mdata_pretty_name = jack_metadatas.pretty_name(uuid)
                pretty_name = pretty_names.pretty_group(
                    client_name, mdata_pretty_name)

                if pretty_name:
                    self.set_metadata(
                        uuid, JackMetadata.PRETTY_NAME, pretty_name)
                    
            for port in self.client.get_ports():
                port_uuid = port.uuid
                if not port_uuid:
                    continue

                mdata_pretty_name = jack_metadatas.pretty_name(uuid)
                pretty_name = pretty_names.pretty_port(
                    port.name, mdata_pretty_name)

                if pretty_name:
                    self.set_metadata(
                        port_uuid, JackMetadata.PRETTY_NAME, pretty_name)

        self.patchbay_manager.sample_rate_changed(
            self.client.samplerate)
        self.patchbay_manager.buffer_size_changed(
            self.client.blocksize)
    
    def check_jack_client_responding(self):
        for i in range(100): # JACK has 5s to answer
            time.sleep(0.050)

            if not self._waiting_jack_client_open:
                break
        else:
            # server never answer
            self.patchbay_manager.server_lose()
            
            # JACK is not responding at all
            # probably it is started but totally bugged
    
    def start_jack_client(self):
        if self.jack_running:
            return
        
        self._waiting_jack_client_open = True
        
        # Sometimes JACK never registers the client
        # and never answers. This thread will allow to exit
        # if JACK didn't answer 5 seconds after register ask
        jack_waiter_thread = threading.Thread(
            target=self.check_jack_client_responding)
        jack_waiter_thread.start()

        fail_info = False

        with suppress_stdout_stderr():
            try:
                self.client = jack.Client('Patchance', no_start_server=True)

            except jack.JackOpenError:
                # We can't log anything here, because stdout is muted
                # by the 'with suppress_stdout_stderr'.
                fail_info = True
                del self.client
                self.client = None
        
        if fail_info:
            # a QTimer can call this method every 500ms
            # so a warning could be annoying here.
            _logger.info('Failed to connect client to JACK server')

        self._waiting_jack_client_open = False
        jack_waiter_thread.join()

        self.jack_running = bool(self.client is not None)

        if self.jack_running:
            self._stopped_sent = False
            self.set_registrations()
            self.init_the_graph()
            self.samplerate = self.client.samplerate
            self.buffer_size = self.client.blocksize
            self.patchbay_manager.server_started()
            self._dsp_timer.start()
            self._transport_timer.start()
            self._check_pretty_timer.start()
        else:
            if not self._stopped_sent:
                self.patchbay_manager.server_stopped()
                self._stopped_sent = True

        self._jack_checker_timer.start()
    
    def _check_pretty_names(self):
        '''Add pretty_name metadatas on newly added clients and ports.
        Note that this metadata is added at least 200ms after the
        client or port apparition. It lets the time to the client owner
        to set itself this metadata,
        then this method decides to overwrite it or not.'''
        if not self.jack_running:
            return
        
        port_names = set[str]()
        client_names = set[str]()
        
        while self._check_pretty_queue.qsize():
            for_client, add, name, add_time = \
                self._check_pretty_queue.queue[0]
            
            if time.time() - add_time < 0.200:
                break
            
            self._check_pretty_queue.get()
            
            if for_client:
                if add: client_names.add(name)
                else: client_names.discard(name)
            else:
                if add: port_names.add(name)
                else: port_names.discard(name)
        
        if self.writes_pretty_names:
            for port_name in port_names:
                try:
                    port = self.client.get_port_by_name(port_name)
                except jack.JackError:
                    continue
                
                value_type = jack.get_property(
                    port.uuid, JackMetadata.PRETTY_NAME)
                if value_type is None:
                    cur_pretty_name = ''
                else:
                    cur_pretty_name = value_type[0]

                pretty_name = self.patchbay_manager.pretty_names.pretty_port(
                    port_name, cur_pretty_name)
                if pretty_name:
                    self.set_metadata(
                        port.uuid, JackMetadata.PRETTY_NAME, pretty_name)
                
        for client_name in client_names:
            try:
                client_uuid = self.client.get_uuid_for_client_name(
                    client_name)
            except jack.JackError:
                continue

            self.patchbay_manager.set_group_uuid_from_name(
                client_name, int(client_uuid))
            
            if not self.writes_pretty_names:
                continue
            
            value_type = jack.get_property(
                client_uuid, JackMetadata.PRETTY_NAME)
            if value_type is None:
                cur_pretty_name = ''
            else:
                cur_pretty_name = value_type[0]
            
            pretty_name = self.patchbay_manager.pretty_names.pretty_group(
                client_name, cur_pretty_name)
            if pretty_name:
                self.set_metadata(
                    int(client_uuid), JackMetadata.PRETTY_NAME, pretty_name)
    
    def _check_dsp(self):
        if not self.jack_running:
            return
        
        current_dsp = math.ceil(self.client.cpu_load())

        if self._dsp_n >= 5:
            self._dsp_n = 0
        
        if self._dsp_n == 0:
            dsp_to_send = max(self._max_dsp_since_last_send, current_dsp)
            
            if dsp_to_send != self._last_dsp_sent:
                self.patchbay_manager.set_dsp_load(dsp_to_send)
                self._last_dsp_sent = dsp_to_send
            
            self._max_dsp_since_last_send = 0
        else:
            self._max_dsp_since_last_send = max(self._max_dsp_since_last_send,
                                                current_dsp)
            
        self._dsp_n += 1

    def _check_transport(self):
        if not self.jack_running:
            return
        
        state, pos_dict = self.client.transport_query()

        transport_position = TransportPosition(
            pos_dict['frame'],
            state == jack.ROLLING,
            'bar' in pos_dict,
            pos_dict.get('bar', 0),
            pos_dict.get('beat', 0),
            pos_dict.get('tick', 0),
            pos_dict.get('beats_per_minute', 0.0))
        
        if transport_position == self._last_transport_pos:
            return
        
        self._last_transport_pos = transport_position
        self.patchbay_manager.refresh_transport(transport_position)

    def is_jack_running(self) -> bool:
        if self.client is None:
            return False
        
        return True
    
    def exit(self):
        if self.client is not None:
            self.client.deactivate()
            self.client.close()
                
    def get_buffer_size(self) -> int:
        if self.client is None:
            return 0
        return self.client.blocksize
    
    def get_sample_rate(self) -> int:
        if self.client is None:
            return 0
        return self.client.samplerate
    
    def set_buffer_size(self, buffer_size: int):
        if self.client is None:
            return
        self.client.blocksize = buffer_size
        
    def connect_ports(self, port_out_name: str, port_in_name: str):
        if self.client is None:
            return
        
        self.client.connect(port_out_name, port_in_name)
    
    def disconnect_ports(self, port_out_name: str, port_in_name: str):
        if self.client is None:
            return
        
        self.client.disconnect(port_out_name, port_in_name)
    
    def set_metadata(self, uuid: int, key: str, mdata: str):
        if mdata == '':
            try:
                self.client.remove_property(uuid, key)
            except:
                _logger.warning(
                    f"Failed to remove property {key} from subject {uuid}.")            
            return
        
        self.client.set_property(uuid, key, mdata, 'text/plain')
    
    def set_registrations(self):
        if self.client is None:
            return

        @self.client.set_client_registration_callback
        def client_registration(name: str, register: bool):
            self._check_pretty_queue.put_nowait(
                (True, register, name, time.time()))

        @self.client.set_port_registration_callback
        def port_registration(port: jack.Port, register: bool):
            port_name = port.name
            
            if register:
                flags = jack._lib.jack_port_flags(port._ptr)
                port_type_int = 0
                if port.is_audio:
                    port_type_int = 1
                elif port.is_midi:
                    port_type_int = 2

                self.patchbay_manager.add_port(
                    port_name, port_type_int, flags, port.uuid)
            else:
                self.patchbay_manager.remove_port(port_name)
            
            self._check_pretty_queue.put_nowait(
                (False, register, port_name, time.time()))
                
        @self.client.set_port_connect_callback
        def port_connect(port_a: jack.Port, port_b: jack.Port, connect: bool):
            if connect:
                self.patchbay_manager.add_connection(
                    port_a.name, port_b.name)
            else:
                self.patchbay_manager.remove_connection(
                    port_a.name, port_b.name)

        @self.client.set_port_rename_callback
        def port_rename(port: JackPort, old: str, new: str):
            if self.writes_pretty_names:
                # if the pretty name seems to have been set by this
                # jack client, we delete the pretty_name metadata
                # because there are big chances that this name is not well now.
                internal_pretty = \
                    self.patchbay_manager.pretty_names.pretty_port(old)
                value_type = jack.get_property(
                    port.uuid, JackMetadata.PRETTY_NAME)
                if value_type is not None:
                    pretty = value_type[0].decode()
                    if pretty == internal_pretty:
                        self.set_metadata(
                            port.uuid, JackMetadata.PRETTY_NAME, '')

            self.patchbay_manager.rename_port(old, new)
            self._check_pretty_queue.put_nowait(
                (False, True, new, time.time()))

        @self.client.set_xrun_callback
        def xrun(delayed_usecs: float):
            self.patchbay_manager.add_xrun()

        @self.client.set_blocksize_callback
        def blocksize(size: int):
            self.patchbay_manager.buffer_size_changed(size)

        @self.client.set_samplerate_callback
        def samplerate(samplerate: int):
            self.patchbay_manager.sample_rate_changed(samplerate)

        try:
            @self.client.set_property_change_callback
            def property_change(subject: int, key: str, change: int):
                value = ''
                
                if change != jack.PROPERTY_DELETED:
                    value_type = jack.get_property(subject, key)
                    if value_type is None:
                        value = ''
                    else:
                        value, type_ = value_type
                        value = value.decode()
                
                self.patchbay_manager.metadata_update(
                    subject, key, value)

        except jack.JackError as e:
            _logger.warning(
                "jack-metadatas are not available,"
                "probably due to the way JACK has been compiled."
                + str(e))
        
        @self.client.set_shutdown_callback
        def on_shutdown(status: jack.Status, reason: str):
            self.jack_running = False
            self.patchbay_manager.server_stopped()
            self._stopped_sent = True

        # jack._lib.jack_set_process_callback(
            # self.client._ptr, C.process_cb, ffi.NULL)
        self.client.activate()
        
    def transport_start(self):
        if self.client is None:
            return
        
        self.client.transport_start()
    
    def transport_pause(self):
        if self.client is None:
            return
        
        self.client.transport_stop()
        
    def transport_stop(self):
        if self.client is None:
            return
        
        self.client.transport_stop()
        self.client.transport_frame = 0
    
    def transport_relocate(self, frame: int):
        if self.client is None:
            return
        
        self.client.transport_frame = frame