from dataclasses import dataclass
from importlib.metadata import metadata
import os
from typing import TYPE_CHECKING, Any

from PyQt5.QtCore import QObject, pyqtSignal

import local_jacklib as jacklib
from local_jacklib.helpers import c_char_p_p_to_list

if TYPE_CHECKING:
    from patchance_pb_manager import PatchancePatchbayManager

PORT_TYPE_NULL = 0
PORT_TYPE_AUDIO = 1
PORT_TYPE_MIDI = 2

def port_type_str_to_port_type(port_type_str: str) -> int:
    if port_type_str == jacklib.JACK_DEFAULT_AUDIO_TYPE:
        return PORT_TYPE_AUDIO
    if port_type_str == jacklib.JACK_DEFAULT_MIDI_TYPE:
        return PORT_TYPE_MIDI
    return PORT_TYPE_NULL


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
        self.jack_client = None
        self.patchbay_manager = patchbay_manager

        with suppress_stdout_stderr():
            self.jack_client = jacklib.client_open(
                "Patchance",
                jacklib.JackNoStartServer | jacklib.JackSessionID,
                None)
        
        if self.jack_client is not None:
            self.set_registrations()
            self.get_all_ports_and_connections()
            self.patchbay_manager.server_started()
    
    @staticmethod
    def get_metadata_value_str(prop: jacklib.Property) -> str:
        value = prop.value
        if isinstance(value, bytes):
            return value.decode()
        elif isinstance(value, str):
            return value
        else:
            try:
                value = str(value)
            except:
                return ''
        return value
    
    def get_all_ports_and_connections(self):
        #get all currents Jack ports and connections
        port_name_list : list[str] = c_char_p_p_to_list(
            jacklib.get_ports(self.jack_client, "", "", 0))
        
        client_names = list[str]()
        jack_ports = list[JackPort]()
        metadatas = list[Metadata]()
        
        for port_name in port_name_list:
            port_ptr = jacklib.port_by_name(self.jack_client, port_name)
            port_type = port_type_str_to_port_type(jacklib.port_type(port_ptr))
            flags = jacklib.port_flags(port_ptr)
            uuid = jacklib.port_uuid(port_ptr)
            
            # self.sg.add_port.emit(port_name, port_type, flags, uuid)
            
            client_name = port_name.partition(':')[0]
            if not client_name in client_names:
                client_names.append(client_name)

            # get port metadatas
            for key in (jacklib.JACK_METADATA_CONNECTED,
                        jacklib.JACK_METADATA_ORDER,
                        jacklib.JACK_METADATA_PORT_GROUP,
                        jacklib.JACK_METADATA_PRETTY_NAME):
                prop = jacklib.get_property(uuid, key)
                if prop is None:
                    continue

                value = self.get_metadata_value_str(prop)
                metadatas.append(Metadata(uuid, key, value))

            if flags & jacklib.JackPortIsInput:
                jack_ports.append(JackPort(port_name, port_type, flags, uuid, []))
                continue
            
            # this port is output, list its connections
            port_conns = list[str]()
            
            for port_con_name in jacklib.port_get_all_connections(
                    self.jack_client, port_ptr):
                port_conns.append(port_con_name)

            jack_ports.append(JackPort(port_name, port_type, flags, uuid, port_conns))
        
        for p in jack_ports:
            self.patchbay_manager.add_port(p.name, p.type, p.flags, p.uuid)
        
        for m in metadatas:
            self.patchbay_manager.metadata_update(m.uuid, m.key, m.value)
        
        for p in jack_ports:
            for in_port_name in p.conns:
                self.patchbay_manager.add_connection(p.name, in_port_name)
        
        for client_name in client_names:
            uuid = jacklib.get_uuid_for_client_name(self.jack_client, client_name)
            if not uuid:
                continue

            self.patchbay_manager.set_group_uuid_from_name(client_name, int(uuid))
            
            # we only look for icon_name now, but in the future other client
            # metadatas could be enabled
            for key in (jacklib.JACK_METADATA_ICON_NAME,):
                prop = jacklib.get_property(
                    int(uuid), jacklib.JACK_METADATA_ICON_NAME)
                if prop is None:
                    continue
                value = self.get_metadata_value_str(prop)
                self.patchbay_manager.metadata_update(int(uuid), key, value)
    
    def jack_client_registration_callback(self, client_name: bytes,
                                          register: int, arg=None) -> int:
        return 0
    
    def jack_port_registration_callback(self, port_id: int, register: bool,
                                        arg=None) -> int:
        
        if self.jack_client is None:
            return
        
        
        port_ptr = jacklib.port_by_id(self.jack_client, port_id)
        port_name = jacklib.port_name(port_ptr)
        
        if register:
            port_type_str = jacklib.port_type(port_ptr)
            port_type = PORT_TYPE_NULL
            
            if port_type_str == jacklib.JACK_DEFAULT_AUDIO_TYPE:
                port_type = PORT_TYPE_AUDIO
            elif port_type_str == jacklib.JACK_DEFAULT_MIDI_TYPE:
                port_type = PORT_TYPE_MIDI
            
            flags = jacklib.port_flags(port_ptr)
            uuid =jacklib.port_uuid(port_ptr)
            self.patchbay_manager.add_port(port_name, port_type, flags, uuid)
        else:
            self.patchbay_manager.remove_port(port_name)

        return 0
    
    def jack_port_connect_callback(self, port_id_A: int, port_id_B: int,
                                   connect_yesno: bool, arg=None) -> int:
        port_ptr_a = jacklib.port_by_id(self.jack_client, port_id_A)
        port_ptr_b = jacklib.port_by_id(self.jack_client, port_id_B)
        
        port_name_a = jacklib.port_name(
            jacklib.port_by_id(self.jack_client, port_id_A))
        port_name_b = jacklib.port_name(
            jacklib.port_by_id(self.jack_client, port_id_B))
        
        if connect_yesno:
            self.patchbay_manager.add_connection(port_name_a, port_name_b)
        else:
            self.patchbay_manager.remove_connection(port_name_a, port_name_b)
        return 0
    
    def jack_port_rename_callback(self, port_id: int, old_name: bytes,
                                  new_name: bytes, arg=None) -> int:
        self.patchbay_manager.rename_port(old_name.decode(), new_name.decode())
        return 0
    
    def jack_xrun_callback(self, arg=None) -> int:
        self.patchbay_manager.add_xrun()
        return 0
    
    def jack_buffer_size_callback(self, buffer_size: int):
        self.patchbay_manager.buffer_size_changed(buffer_size)
        return 0
    
    def jack_sample_rate_callback(self, samplerate, arg=None) -> int:
        self.patchbay_manager.sample_rate_changed(samplerate)
        return 0
    
    def jack_properties_change_callback(self, uuid: int, name: bytes,
                                        type_: int, arg=None) -> int:
        if name is not None:
            name = name.decode()
        
        value = ''

        if name and type_ != jacklib.PropertyDeleted:
            prop = jacklib.get_property(uuid, name)
            if prop is None:
                return 0
            
            value = self.get_metadata_value_str(prop)
        
        self.patchbay_manager.metadata_update(int(uuid), name, value)
        
        return 0
    
    def jack_shutdown_callback(self, arg=None) -> int:
        return 0
    
    def set_registrations(self):
        if not self.jack_client:
            return
        
        jacklib.set_client_registration_callback(
            self.jack_client, self.jack_client_registration_callback, None)
        jacklib.set_port_registration_callback(
            self.jack_client, self.jack_port_registration_callback, None)
        jacklib.set_port_connect_callback(
            self.jack_client, self.jack_port_connect_callback, None)
        jacklib.set_port_rename_callback(
            self.jack_client, self.jack_port_rename_callback, None)
        jacklib.set_xrun_callback(
            self.jack_client, self.jack_xrun_callback, None)
        jacklib.set_buffer_size_callback(
            self.jack_client, self.jack_buffer_size_callback, None)
        jacklib.set_sample_rate_callback(
            self.jack_client, self.jack_sample_rate_callback, None)
        jacklib.set_property_change_callback(
            self.jack_client, self.jack_properties_change_callback, None)
        jacklib.on_shutdown(
            self.jack_client, self.jack_shutdown_callback, None)
        jacklib.activate(self.jack_client)