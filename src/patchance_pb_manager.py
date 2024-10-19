
import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Union

from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QApplication

from patchbay import (
    CanvasMenu,
    Callbacker,
    CanvasOptionsDialog,
    PatchbayManager)
from patchbay.patchcanvas.patshared import (
    PortType, PortTypesViewFlag, from_json_to_str)

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
        
    def _ports_connect(self, group_out_id: int, port_out_id: int,
                       group_in_id: int, port_in_id: int):
        port_out = self.mng.get_port_from_id(group_out_id, port_out_id)
        port_in = self.mng.get_port_from_id(group_in_id, port_in_id)
        if port_out is None or port_in is None:
            return
        
        if port_out.type is PortType.MIDI_ALSA:
            if self.mng.alsa_mng is None:
                return
        
            self.mng.alsa_mng.connect_ports(port_out.full_name, port_in.full_name)
        if self.mng.jack_mng is None:
            return
        
        self.mng.jack_mng.connect_ports(port_out.full_name, port_in.full_name)

    def _ports_disconnect(self, connection_id: int):
        for conn in self.mng.connections:
            if conn.connection_id == connection_id:
                if conn.port_type() is PortType.MIDI_ALSA:
                    if self.mng.alsa_mng is None:
                        return
                    
                    self.mng.alsa_mng.connect_ports(
                        conn.port_out.full_name,
                        conn.port_in.full_name,
                        disconnect=True)
                    return

                self.mng.jack_mng.disconnect_ports(
                    conn.port_out.full_name, conn.port_in.full_name)
                return


class PatchancePatchbayManager(PatchbayManager):
    def __init__(self, settings: Union[QSettings, None] =None):
        super().__init__(settings)
        self._settings = settings
        
        self.jack_mng = None
        self.alsa_mng = None
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

        self.sg.views_changed.emit()
        
    
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
        if self.jack_mng is not None:
            self.jack_mng.init_the_graph()
        
        if self.alsa_mng is not None:
            self.alsa_mng.add_all_ports()
    
    def change_buffersize(self, buffer_size: int):
        super().change_buffersize(buffer_size)
        self.jack_mng.set_buffer_size(buffer_size)
    
    def transport_play_pause(self, play: bool):
        if play:
            self.jack_mng.transport_start()
        else:
            self.jack_mng.transport_pause()
        
    def transport_stop(self):
        self.jack_mng.transport_stop()

    def transport_relocate(self, frame: int):
        self.jack_mng.transport_relocate(frame)

    def set_alsa_midi_enabled(self, yesno: int):
        if self.alsa_mng is not None:    
            if yesno:
                self.alsa_mng.add_all_ports()
            else:
                self.alsa_mng.stop_events_loop()
        
        super().set_alsa_midi_enabled(yesno)

    def finish_init(self, main: 'Main'):
        self.jack_mng = main.jack_manager
        self.alsa_mng = main.alsa_manager
        self.set_main_win(main.main_win)
        self._setup_canvas()

        self.set_canvas_menu(CanvasMenu(self))
        self.set_tools_widget(main.main_win.patchbay_tools)
        self.set_filter_frame(main.main_win.ui.filterFrame)
        
        if self.jack_mng.jack_running:
            self.server_started()
            self.sample_rate_changed(self.jack_mng.get_sample_rate())
            self.buffer_size_changed(self.jack_mng.get_buffer_size())
        else:
            self.server_stopped()

        self.set_options_dialog(
            CanvasOptionsDialog(self.main_win, self, self._settings))

    def save_positions(self):
        json_str = from_json_to_str(
            {'views': self.views.to_json_list(),
             'portgroups': self.portgroups_memory.to_json()})

        if self._memory_path is not None:
            try:
                with open(self._memory_path, 'w') as f:
                    f.write(json_str)
            except Exception as e:
                _logger.warning(str(e))

