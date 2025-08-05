
import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Union

from qtpy.QtCore import QSettings
from qtpy.QtWidgets import QApplication
from patch_engine.patch_engine import PatchEngine
from patchbay.bases.elements import CanvasOptimizeIt

from patchbay import (
    CanvasMenu,
    Callbacker,
    CanvasOptionsDialog,
    PatchbayManager)
from patshared import (
    PortType, PortTypesViewFlag, from_json_to_str, Naming)

from tools import get_code_root
import xdg

if TYPE_CHECKING:
    from main_win import MainWindow
    from patchance import Main

_logger = logging.getLogger(__name__)

MEMORY_FILE = 'canvas.json'


class PatchanceCallbacker(Callbacker):
    def __init__(self, manager: 'PatchancePatchbayManager'):
        super().__init__(manager)

        if TYPE_CHECKING:
            self.mng = manager
    
    def _group_rename(
            self, group_id: int, custom_name: str, save_in_jack: bool):
        if not save_in_jack:
            return

        group = self.mng.get_group_from_id(group_id)
        if group is None:
            return

        
        if not group.uuid:
            return
        
        self.mng.pe.write_group_pretty_name(group.name, custom_name)

    def _port_rename(
            self, group_id: int, port_id: int,
            custom_name: str, save_in_jack: bool):
        if not save_in_jack:
            return

        port = self.mng.get_port_from_id(group_id, port_id)
        if port is None:
            return

        if port.type.is_jack:
            self.mng.pe.write_port_pretty_name(port.full_name, custom_name)

    def _ports_connect(self, group_out_id: int, port_out_id: int,
                       group_in_id: int, port_in_id: int):
        port_out = self.mng.get_port_from_id(group_out_id, port_out_id)
        port_in = self.mng.get_port_from_id(group_in_id, port_in_id)
        if port_out is None or port_in is None:
            return
        
        self.mng.pe.connect_ports(port_out.full_name, port_in.full_name)        
        
        

    def _ports_disconnect(self, connection_id: int):
        for conn in self.mng.connections:
            if conn.connection_id == connection_id:
                self.mng.pe.connect_ports(
                    conn.port_out.full_name,
                    conn.port_in.full_name,
                    disconnect=True)
                return


class PatchancePatchbayManager(PatchbayManager):
    def __init__(self, engine: PatchEngine,
                 settings: Union[QSettings, None] =None):
        super().__init__(settings)
        self.pe = engine
        self._settings = settings
        
        self._memory_path = None

        self._load_memory_file()

    def _load_memory_file(self):
        if self._settings is None:
            return
        
        self._memory_path = \
            Path(self._settings.fileName()).parent.joinpath(MEMORY_FILE)

        no_file_to_load = False

        try:
            with open(self._memory_path, 'r') as f:                
                json_dict = json.load(f)
                assert isinstance(json_dict, dict)

        except FileNotFoundError:
            _logger.warning(
                f"File {self._memory_path} has not been found, "
                "It is probably the first startup.")
            no_file_to_load = True

        except:
            _logger.warning(
                f"File {self._memory_path} is incorrectly written, "
                "it will be ignored.")
            no_file_to_load = True
        
        self.view_number = 1

        if no_file_to_load:
            return
        
        if json_dict.get('views') is not None:
            self.views.eat_json_list(json_dict.get('views'), clear=True)
        
        elif json_dict.get('group_positions') is not None:
            group_positions: list[dict] = json_dict.get('group_positions')
            higher_ptv_int = (PortTypesViewFlag.AUDIO
                              | PortTypesViewFlag.MIDI
                              | PortTypesViewFlag.CV).value

            for gpos_dict in group_positions:
                higher_ptv_int = max(
                    higher_ptv_int, gpos_dict['port_types_view'])

            for gpos_dict in group_positions:
                if gpos_dict['port_types_view'] == higher_ptv_int:
                    gpos_dict['port_types_view'] = PortTypesViewFlag.ALL.value
                
                self.views.add_old_json_gpos(gpos_dict)
        
        self.view_number = self.views.first_view_num()

        self.portgroups_memory.eat_json(json_dict.get('portgroups'))
        self.custom_names.eat_json(json_dict.get('custom_names'))

        self.sg.views_changed.emit()
        self.change_port_types_view(
            self.views[self.view_number].default_port_types_view)
    
    def _setup_canvas(self):
        SUBMODULE = 'HoustonPatchbay'
        THEME_PATH = Path(SUBMODULE) / 'themes'
        source_theme_path = Path(get_code_root()) / THEME_PATH
        manual_path = Path(get_code_root()) / SUBMODULE / 'manual'
        theme_paths = list[Path]()
        
        app_title = QApplication.applicationName().lower()
        
        theme_paths.append(xdg.xdg_data_home() / app_title / THEME_PATH)

        if source_theme_path.exists():
            theme_paths.append(source_theme_path)

        for p in xdg.xdg_data_dirs():
            path = p / app_title / THEME_PATH
            if path not in theme_paths:
                theme_paths.append(path)

        if TYPE_CHECKING:
            assert isinstance(self.main_win, MainWindow)

        self.app_init(self.main_win.ui.graphicsView,
                      theme_paths,
                      manual_path=manual_path,
                      callbacker=PatchanceCallbacker(self),
                      default_theme_name='Yellow Boards')

    def refresh(self):
        super().refresh()
        self.pe.refresh()

    def change_buffersize(self, buffer_size: int):
        super().change_buffersize(buffer_size)
        self.pe.set_buffer_size(buffer_size)
    
    def transport_play_pause(self, play: bool):
        self.pe.transport_play(play)
        
    def transport_stop(self):
        self.pe.transport_stop()

    def transport_relocate(self, frame: int):
        self.pe.transport_relocate(frame)

    def set_alsa_midi_enabled(self, yesno: int):
        
        super().set_alsa_midi_enabled(yesno)

    def export_custom_names_to_jack(self):
        self.pe.export_all_custom_names_to_jack_now()

    def import_pretty_names_from_jack(self):
        clients_dict, ports_dict = \
            self.pe.import_all_pretty_names_from_jack()
        
        for client_name, pretty_name in clients_dict.items():
            self.custom_names.save_group(client_name, pretty_name)
        
        for port_name, pretty_name in ports_dict.items():
            self.custom_names.save_port(port_name, pretty_name)

    def change_jack_export_naming(self, naming: Naming):
        self._settings.setValue('Canvas/jack_export_naming', naming.name)
        self.jack_export_naming = naming
        auto_export = Naming.CUSTOM in naming
        self.pe.set_pretty_names_auto_export(auto_export)

    def server_restarted(self):
        self.sample_rate_changed(self.pe.samplerate)
        self.buffer_size_changed(self.pe.buffer_size)
        
        with CanvasOptimizeIt(self):
            for port in self.pe.ports:
                self.add_port(port.name, port.type, port.flags, port.uuid)
            
            for client_name, client_uuid in self.pe.client_name_uuids.items():
                self.set_group_uuid_from_name(client_name, client_uuid)
            
            for connection in self.pe.connections:
                self.add_connection(*connection)
            
            for uuid, key_dict in self.pe.metadatas.items():
                for key, value in key_dict.items():
                    self.metadata_update(uuid, key, value)

    def finish_init(self, main: 'Main'):
        self.set_main_win(main.main_win)
        self._setup_canvas()

        self.set_canvas_menu(CanvasMenu(self))
        self.set_tools_widget(main.main_win.patchbay_tools)
        self.set_filter_frame(main.main_win.ui.filterFrame)
        

        self.set_options_dialog(
            CanvasOptionsDialog(self.main_win, self))

    def save_positions(self):
        '''Save patchbay boxes positions and custom names'''
        json_str = from_json_to_str(
            {'views': self.views.to_json_list(),
             'portgroups': self.portgroups_memory.to_json(),
             'custom_names': self.custom_names.to_json()})

        if self._memory_path is not None:
            try:
                with open(self._memory_path, 'w') as f:
                    f.write(json_str)
            except Exception as e:
                _logger.warning(str(e))

