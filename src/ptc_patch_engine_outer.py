from patch_engine import PatchEngineOuter
from patshared import TransportPosition

from patchance_pb_manager import PatchancePatchbayManager

class PtcPatchEngineOuter(PatchEngineOuter):
    def __init__(self, mng: PatchancePatchbayManager):
        super().__init__()
        self.mng = mng
        
    def associate_client_name_and_uuid(self, client_name: str, uuid: int):
        self.mng.set_group_uuid_from_name(client_name, uuid)
    def port_added(self, pname: str, ptype: int, pflags: int, puuid: int):
        self.mng.add_port(pname, ptype, pflags, puuid)
    def port_renamed(self, ex_name: str, new_name: str, uuid=0):
        self.mng.rename_port(ex_name, new_name, uuid=uuid)
    def port_removed(self, port_name: str):
        self.mng.remove_port(port_name)
    def metadata_updated(self, uuid: int, key: str, value: str):
        self.mng.metadata_update(uuid, key, value)
    def connection_added(self, connection: tuple[str, str]):
        self.mng.add_connection(*connection)
    def connection_removed(self, connection: tuple[str, str]):
        self.mng.remove_connection(*connection)
    def server_stopped(self):
        self.mng.server_stopped()
    def send_transport_position(self, tpos: TransportPosition):
        self.mng.refresh_transport(tpos)
    def send_dsp_load(self, dsp_load: int):
        self.mng.set_dsp_load(dsp_load)
    def send_one_xrun(self):
        self.mng.add_xrun()
    def send_buffersize(self, buffer_size: int):
        self.mng.buffer_size_changed(buffer_size)
    def send_samplerate(self, samplerate: int):
        self.mng.sample_rate_changed(samplerate)
    def send_pretty_names_locked(self, locked: bool):
        if self.mng.options_dialog is not None:
            self.mng.options_dialog.set_pretty_names_locked(locked)
    def send_server_lose(self):
        self.mng.server_lose()
    def server_restarted(self):
        self.mng.server_restarted()
    def make_one_shot_act(self, one_shot_act: str):...