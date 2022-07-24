
from enum import IntEnum
import json
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union
import time
import os
import sys

from PyQt5.QtCore import QLocale, QUrl, QSettings, pyqtSignal, QObject
from PyQt5.QtGui import QDesktopServices

from .patchbay.patchcanvas.init_values import CallbackAct, PortType

from .patchbay.patchbay_manager import PatchbayManager
from .patchbay.base_elements import (Group, GroupPos, PortgroupMem,
                                     PortMode, BoxLayoutMode)
from .patchbay.options_dialog import CanvasOptionsDialog
from .patchbay.tools_widgets import PatchbayToolsWidget, CanvasMenu
from .patchbay.calbacker import Callbacker
from .patchbay.patchcanvas import patchcanvas


from .tools import get_code_root

if TYPE_CHECKING:
    from .main_win import MainWindow
    from patchance import Main


class SignalObject(QObject):
    callback_sig = pyqtSignal(IntEnum, tuple)


class PatchancePatchbayManager(PatchbayManager):
    def __init__(self, settings: Union[QSettings, None] =None):
        super().__init__(settings)
        self.sgc = SignalObject()
        self.callbacker = Callbacker(self)
        self.sgc.callback_sig.connect(self.callbacker.receive)
        self._settings = settings
    
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
    
    def finish_init(self, main: 'Main'):
        self.set_main_win(main.main_win)
        self._setup_canvas()
        self.set_canvas_menu(CanvasMenu(self))
        self.set_tools_widget(main.main_win.ui.patchbayToolsWidget)
        # self.set_canvas_menu(RayCanvasMenu(self))
        
        options_dialog = CanvasOptionsDialog(self.main_win, self._settings)
        # options_dialog.set_user_theme_icon(
        #     RayIcon('im-user', is_dark_theme(options_dialog)))
        self.set_options_dialog(options_dialog)

