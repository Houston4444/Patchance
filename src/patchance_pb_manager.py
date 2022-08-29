
import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Union

from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QApplication

from patchbay.base_elements import GroupPos, PortgroupMem
from patchbay import (
    CanvasMenu,
    Callbacker,
    CanvasOptionsDialog,
    PatchbayManager)

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
        
        if self.mng.jack_mng is None:
            return
        
        self.mng.jack_mng.connect_ports(port_out.full_name, port_in.full_name)

    def _ports_disconnect(self, connection_id: int):
        for conn in self.mng.connections:
            if conn.connection_id == connection_id:
                self.mng.jack_mng.disconnect_ports(
                    conn.port_out.full_name, conn.port_in.full_name)
                break


class PatchancePatchbayManager(PatchbayManager):
    def __init__(self, settings: Union[QSettings, None] =None):
        super().__init__(settings)
        self._settings = settings
        
        self.jack_mng = None
        self._memory_path = None
        
        if settings is not None:
            self._memory_path = Path(settings.fileName()).parent.joinpath(MEMORY_FILE)

            try:
                with open(self._memory_path, 'r') as f:                
                    json_dict = json.load(f)
                    assert isinstance(json_dict, dict)
            except FileNotFoundError:
                _logger.warning(f"File {self._memory_path} has not been found,"
                                "It is probably the first startup.")
                return
            except:
                _logger.warning(f"File {self._memory_path} is incorrectly written"
                                "it will be ignored.")
                return
            
            if 'group_positions' in json_dict.keys():
                gposs = json_dict['group_positions']

                for gpos in gposs:
                    if isinstance(gpos, dict):
                        self.group_positions.append(GroupPos.from_serialized_dict(gpos))
            
            if 'portgroups' in json_dict.keys():
                pg_mems = json_dict['portgroups']

                for pg_mem_dict in pg_mems:
                    self.portgroups_memory.append(
                        PortgroupMem.from_serialized_dict(pg_mem_dict))
    
    def _setup_canvas(self):
        SUBMODULE = 'HoustonPatchbay'
        THEME_PATH = Path(SUBMODULE) / 'themes'
        source_theme_path = Path(get_code_root()) / THEME_PATH
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
                      callbacker=PatchanceCallbacker(self),
                      default_theme_name='Yellow Boards')

    def refresh(self):
        super().refresh()
        if self.jack_mng is not None:
            self.jack_mng.init_the_graph()
    
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

    def finish_init(self, main: 'Main'):
        self.jack_mng = main.jack_manager
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

        self.set_options_dialog(CanvasOptionsDialog(self.main_win, self, self._settings))

    def save_positions(self):        
        gposs_as_dicts = [gpos.as_serializable_dict()
                          for gpos in self.group_positions]
        pg_mems_as_dict = [pg_mem.as_serializable_dict()
                           for pg_mem in self.portgroups_memory]
        
        full_dict = {'group_positions': gposs_as_dicts,
                     'portgroups': pg_mems_as_dict}
        
        if self._memory_path is not None:
            try:
                with open(self._memory_path, 'w') as f:
                    json.dump(full_dict, f, indent=4)
            except Exception as e:
                _logger.warning(str(e))

