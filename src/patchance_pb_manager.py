
import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Union

from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QApplication

from patchbay.base_elements import (
    GroupPos,
    PortgroupMem,
    PortTypesViewFlag,
    PortType)
from patchbay import (
    CanvasMenu,
    Callbacker,
    CanvasOptionsDialog,
    PatchbayManager)
from patchbay.patchcanvas.base_enums import (
    from_json_to_str, portgroups_mem_from_json, portgroups_memory_to_json)

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
            self.views[self.view_number] = {}
            return

        group_positions: list[dict] = json_dict.get('group_positions')
        views: dict = json_dict.get('views')
        
        if isinstance(views, list):
            indexes = set[int]()
            missing_indexes = set[int]()
            
            # first check for missing or duplicate indexes
            for v_dict in views:
                if not isinstance(v_dict, dict):
                    _logger.warning('View is not a dict')
                    continue
                
                index = v_dict.get('index')
                if not isinstance(index, int) or index in indexes:
                    missing_indexes.add(views.index(v_dict))
                else:
                    indexes.add(index)

            if missing_indexes:
                missing_list = sorted(missing_indexes)
                for i in missing_list:
                    index = i + 1
                    while index in indexes:
                        index += 1
                    self.views[i]['index'] = index
                    indexes.add(index)
            
            # now we can assume all views have an index
            # let's parse the list of dicts
            for v_dict in views:
                if not isinstance(v_dict, dict):
                    continue
                
                view_number = v_dict['index']
                self.views[view_number] = {}
                name = v_dict.get('name')
                port_types_str = v_dict.get('default_port_types')
                is_white_list = v_dict.get('is_white_list')
                
                if isinstance(name, str):
                    self.write_view_data(view_number, name=name)

                if isinstance(port_types_str, str):
                    default_port_types = PortTypesViewFlag.from_config_str(
                        port_types_str)
                    self.write_view_data(
                        view_number, port_types=default_port_types)

                if is_white_list is not None:
                   self.write_view_data(
                       view_number, white_list_view=bool(is_white_list)) 
                
                for ptv_str, ptv_dict in v_dict.items():
                    if not isinstance(ptv_dict, dict):
                        continue
                    
                    if not (isinstance(ptv_str, str)):
                        continue
                    
                    ptv = PortTypesViewFlag.from_config_str(ptv_str)
                    if not ptv:
                        continue
                    
                    self.views[view_number][ptv] = {}
                    
                    for group_name, gpos_dict in ptv_dict.items():
                        if not isinstance(gpos_dict, dict):
                            continue
                        
                        if not isinstance(group_name, str):
                            continue
                        
                        self.views[view_number][ptv][group_name] = \
                            GroupPos.from_new_dict(ptv, group_name, gpos_dict)

            self.sort_views_by_index()

            for view_key in self.views.keys():
                # select the first view
                self.view_number = view_key
                break
            else:
                # no views in the file, write an empty view
                self.views[self.view_number] = {}

        elif isinstance(group_positions, list):
            self.views[self.view_number] = {}

            higher_ptv_int = (PortTypesViewFlag.AUDIO
                              | PortTypesViewFlag.MIDI
                              | PortTypesViewFlag.CV).value

            for gpos_dict in group_positions:
                higher_ptv_int = max(
                    higher_ptv_int, gpos_dict['port_types_view'])

            for gpos_dict in group_positions:
                if gpos_dict['port_types_view'] == higher_ptv_int:
                    gpos_dict['port_types_view'] = PortTypesViewFlag.ALL.value

                gpos = GroupPos.from_serialized_dict(gpos_dict)
                ptv_dict = self.views[self.view_number].get(gpos.port_types_view)
                if ptv_dict is None:
                    ptv_dict = {}
                    self.views[self.view_number][gpos.port_types_view] = ptv_dict
                
                ptv_dict[gpos.group_name] = gpos

        else:
            self.views[self.view_number] = {}

        self.sg.views_changed.emit()
        
        if 'portgroups' in json_dict.keys():
            self.portgroups_memory = portgroups_mem_from_json(
                json_dict['portgroups'])
    
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

        self.set_options_dialog(CanvasOptionsDialog(self.main_win, self, self._settings))

    def save_positions(self):
        full_dict = {'portgroups': portgroups_memory_to_json(
            self.portgroups_memory)}
        
        self.sort_views_by_index()
        views = []

        for view_number, ptv_dict in self.views.items():
            view_item = {}
            view_item['index'] = view_number

            view_data = self.views_datas.get(view_number)
            if view_data is not None:
                if view_data.name:
                    view_item['name'] = view_data.name
                view_item['default_port_types'] = \
                    view_data.default_port_types_view.to_config_str()
                if view_data.is_white_list:
                    view_item['is_white_list'] = True
                        
            for ptv, pt_dict in ptv_dict.items():
                ptv_str = ptv.to_config_str()
                if not ptv_str:
                    continue
                
                view_item[ptv_str] = {}

                for group_name, gpos in pt_dict.items():
                    if gpos.has_sure_existence:
                        view_item[ptv_str][group_name] = gpos.as_new_dict()
            views.append(view_item)

        full_dict['views'] = views
        
        json_str = from_json_to_str(full_dict)

        if self._memory_path is not None:
            try:
                with open(self._memory_path, 'w') as f:
                    f.write(json_str)
            except Exception as e:
                _logger.warning(str(e))

