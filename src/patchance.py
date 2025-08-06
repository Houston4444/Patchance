#!/usr/bin/env -S python3 -u

APP_TITLE = 'Patchance'
VERSION = (1, 2, 0)

import sys
from pathlib import Path
from typing import Optional

# manage arguments now
# Yes, that is not conventional to do this kind of code during imports
# but it allows faster answer for --version and --help argument.
reading_cfg_dir = False
config_dir: Optional[Path] = None

for arg in sys.argv[1:]:
    match arg:
        
        case '--config-dir'|'-c':
            reading_cfg_dir = True
        
        case '--export-custom-names'|'-c2p'\
                |'--import-pretty-names'|'-p2c'\
                |'--clear-pretty-names':
            if config_dir is None:
                import xdg
                config_dir = xdg.xdg_config_home() / APP_TITLE

            import one_shot_pretty_act
            one_shot_pretty_act.make_one_shot_act(arg, config_dir)
        
        case '--version':
            sys.stdout.write('.'.join([str(i) for i in VERSION]) + '\n')
            sys.exit(0)

        case '--help':
            info = (
                "Patchbay application for JACK\n"
                "Usage: patchance [--help] [--version]\n"
                "  --config-dir CONFIG_DIR, -c CONFIG_DIR\n"
                "             use a custom config directory\n"
                "  --export-custom-names, -c2p\n"
                "             export custom names from config to JACK pretty-names and exit\n"
                "  --import-pretty-names, -p2c\n"
                "             import JACK pretty-names to custom names, save config and exit\n"
                "  --clear-pretty-names\n"
                "             delete all JACK pretty-name metadatas and exit\n"
                "  --help     show this help\n"
                "  --version  print program version\n"
            )
            sys.stdout.write(info)
            sys.exit(0)
            
        case _ if reading_cfg_dir:
            config_dir = Path(arg).expanduser()
            try:
                config_dir.mkdir(parents=True, exist_ok=True)
            except BaseException as e:
                sys.stderr.write(
                    f'Impossible to create config dir {config_dir}\n'
                    f'{str(e)}\n')
                sys.exit(1)

import os
import signal
import logging
from dataclasses import dataclass

# add HoustonPatchbay as lib
sys.path.insert(1, str(Path(__file__).parents[1] / 'HoustonPatchbay/source'))

from qt_api import QT_API

# Needed for qtpy to know if it should use PyQt5 or PyQt6
os.environ['QT_API'] = QT_API

from qtpy.QtWidgets import QApplication
from qtpy.QtGui import QIcon, QFontDatabase
from qtpy.QtCore import QLocale, QTranslator, QTimer, QLibraryInfo, QSettings, QObject

from patshared import Naming, custom_names
from patch_engine import PatchEngine, ALSA_LIB_OK

from engine_loop import PatchTimeoutObj
from main_win import MainWindow
from patchance_pb_manager import PatchancePatchbayManager
from ptc_patch_engine_outer import PtcPatchEngineOuter


@dataclass
class Main:
    app: QApplication
    main_win: MainWindow
    patchbay_manager: PatchancePatchbayManager
    settings: QSettings



        
def signal_handler(sig, frame):
    if sig in (signal.SIGINT, signal.SIGTERM):
        QApplication.quit()

def get_code_root():
    return str(Path(__file__).parents[1])

def make_logger():
    logger = logging.getLogger(__name__)
    log_handler = logging.StreamHandler()
    log_handler.setFormatter(logging.Formatter(
        f"%(name)s - %(levelname)s - %(message)s"))
    logger.setLevel(logging.WARNING)
    logger.addHandler(log_handler)

def main_loop():
    global main
    
    make_logger()
    
    import resources_rc
    
    app = QApplication(sys.argv)
    app.setApplicationName(APP_TITLE)
    app.setApplicationVersion('.'.join([str(i) for i in VERSION]))
    app.setOrganizationName(APP_TITLE)
    app.setWindowIcon(QIcon(
        f':/main_icon/scalable/{APP_TITLE.lower()}.svg'))
    app.setDesktopFileName(APP_TITLE.lower())
    
    ### Translation process
    app_translator = QTranslator()
    if app_translator.load(QLocale(), APP_TITLE.lower(),
                           '_', "%s/locale" % get_code_root()):
        app.installTranslator(app_translator)

    patchbay_translator = QTranslator()
    if patchbay_translator.load(QLocale(), 'patchbay',
                                '_', "%s/HoustonPatchbay/locale" % get_code_root()):
        app.installTranslator(patchbay_translator)

    sys_translator = QTranslator()
    path_sys_translations = QLibraryInfo.location(QLibraryInfo.TranslationsPath)
    if sys_translator.load(QLocale(), 'qt', '_', path_sys_translations):
        app.installTranslator(sys_translator)

    QFontDatabase.addApplicationFont(":/fonts/Ubuntu-R.ttf")
    QFontDatabase.addApplicationFont(":/fonts/Ubuntu-C.ttf")

    #connect signals
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    #needed for signals SIGINT, SIGTERM
    timer = QTimer()
    timer.start(200)
    timer.timeout.connect(lambda: None)

    if config_dir is not None:
        settings = QSettings(
            str(config_dir / f'{APP_TITLE}.conf'),
            QSettings.Format.IniFormat)
    else:
        settings = QSettings()

    main_win = MainWindow()
    
    export_naming = Naming.from_config_str(
        settings.value(
            'Canvas/jack_export_naming', 'TRUE_NAME', type=str))        
    engine = PatchEngine(
        'Patchance', Path('/tmp/Patchance/pretty_names.json'),
        Naming.CUSTOM in export_naming)
    pb_manager = PatchancePatchbayManager(engine, settings)
    pb_manager.jack_export_naming = export_naming
    engine.custom_names = pb_manager.custom_names

    main = Main(app,
                main_win,
                pb_manager,
                settings)

    pb_manager.finish_init(main)
    if not ALSA_LIB_OK:
        pb_manager.options_dialog.enable_alsa_midi(False)
    
    timeout_obj = PatchTimeoutObj(engine)
    patch_timer = QTimer()
    patch_timer.timeout.connect(timeout_obj.check_patch)
    
    main_win.finish_init(main)
    main_win.show()

    engine.start(PtcPatchEngineOuter(pb_manager))
    engine.apply_pretty_names_export()
    patch_timer.start(50)

    app.exec()
    settings.sync()
    pb_manager.save_positions()
    
    patch_timer.stop()
    engine.exit()
    del app


if __name__ == '__main__':
    main_loop()
