
from enum import IntEnum
import json
from pathlib import Path
from typing import TYPE_CHECKING, Union
from unittest.mock import patch

from PyQt5.QtCore import QSettings, pyqtSignal, QObject


from .patchbay.base_elements import GroupPos, PortgroupMem
from .patchbay.patchcanvas.init_values import CallbackAct
from .patchbay.patchbay_manager import PatchbayManager
from .patchbay.options_dialog import CanvasOptionsDialog
from .patchbay.tools_widgets import PatchbayToolsWidget, CanvasMenu
from .patchbay.calbacker import Callbacker
from .patchbay.patchcanvas import patchcanvas


from .tools import get_code_root

if TYPE_CHECKING:
    from .main_win import MainWindow
    from patchance import Main


MEMORY_FILE = 'canvas.json'


class SignalObject(QObject):
    callback_sig = pyqtSignal(IntEnum, tuple)


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
        self.sgc = SignalObject()
        self.callbacker = PatchanceCallbacker(self)
        self.sgc.callback_sig.connect(self.callbacker.receive)
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
                print('fichier introuvab')
                return
            except:
                print('ça va pas ton fichier')
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
        
    
    def canvas_callback(self, action: CallbackAct, *args):
        self.sgc.callback_sig.emit(action, args)
    
    def _setup_canvas(self):
        options = patchcanvas.CanvasOptionsObject()
        options.theme_name = self._settings.value(
            'Canvas/theme', 'Black Gold', type=str)
        options.eyecandy = patchcanvas.EyeCandy.NONE
        if self._settings.value('Canvas/box_shadows', False, type=bool):
            options.eyecandy = patchcanvas.EyeCandy.SMALL

        options.auto_hide_groups = True
        options.auto_select_items = False
        options.inline_displays = False
        options.elastic = self._settings.value('Canvas/elastic', True, type=bool)
        options.prevent_overlap = self._settings.value(
            'Canvas/prevent_overlap', True, type=bool)
        options.max_port_width = self._settings.value(
            'Canvas/max_port_width', 160, type=int)

        features = patchcanvas.CanvasFeaturesObject()
        features.group_info = False
        features.group_rename = False
        features.port_info = True
        features.port_rename = False
        features.handle_group_pos = False

        theme_paths = list[Path]()
        theme_paths.append(
            Path(self._settings.fileName()).parent.joinpath('patchbay_themes'))
        theme_paths.append(
            Path(get_code_root()).joinpath('HoustonPatchbay','themes'))

        patchcanvas.set_options(options)
        patchcanvas.set_features(features)

        if TYPE_CHECKING:
            assert isinstance(self.main_win, MainWindow)

        patchcanvas.init(
            'Patchance', self.main_win.scene,
            self.canvas_callback,
            tuple(theme_paths))
        patchcanvas.set_semi_hide_opacity(
            self._settings.value(
                'Canvas/semi_hide_opacity', 0.17, type=float))
    
    def refresh(self):
        super().refresh()
        if self.jack_mng is not None:
            self.jack_mng.init_the_graph()
        
    
    def finish_init(self, main: 'Main'):
        self.jack_mng = main.jack_manager
        self.set_main_win(main.main_win)
        self._setup_canvas()
        self.set_canvas_menu(CanvasMenu(self))
        self.set_tools_widget(main.main_win.ui.patchbayToolsWidget)
        
        if self.jack_mng.jack_running:
            self.server_started()
            self.sample_rate_changed(self.jack_mng.get_sample_rate())
            self.buffer_size_changed(self.jack_mng.get_buffer_size())
        else:
            self.server_stopped()
        
        self.set_options_dialog(CanvasOptionsDialog(self.main_win, self._settings))
    
    def save_positions(self):
        for gpos in self.group_positions:
            print(gpos.group_name, gpos.layout_modes)
        
        gposs_as_dicts = [gpos.as_serializable_dict() for gpos in self.group_positions]
        pg_mems_as_dict = [pg_mem.as_serializable_dict()
                           for pg_mem in self.portgroups_memory]
        
        full_dict = {'group_positions': gposs_as_dicts,
                     'portgroups': pg_mems_as_dict}
        
        if self._memory_path is not None:
            try:
                with open(self._memory_path, 'w') as f:
                    json.dump(full_dict, f, indent=4)
            except Exception as e:
                print(e)
                

