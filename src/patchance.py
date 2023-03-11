#!/usr/bin/python3 -u

APP_TITLE = 'Patchance'
VERSION = (1, 0, 0)

import sys

# manage arguments now
# Yes, that is not conventional to do this kind of code during imports
# but it allows faster answer for --version argument.
for arg in sys.argv[1:]:
    if arg == '--version':
        sys.stdout.write('.'.join([str(i) for i in VERSION]) + '\n')
        sys.exit(0)
    if arg == '--help':
        info = (
            "Patchbay application for JACK\n"
            "Usage: patchance [--help] [--version]\n"
            "  --help     show this help\n"
            "  --version  print program version\n"
        )
        sys.stdout.write(info)
        sys.exit(0)


from typing import Optional
import signal
import logging

from dataclasses import dataclass
from os.path import dirname


from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon, QFontDatabase
from PyQt5.QtCore import QLocale, QTranslator, QTimer, QLibraryInfo, QSettings

try:
    from pyalsa.alsaseq import SEQ_LIB_VERSION_STR
    ALSA_VERSION_LIST = [int(num) for num in SEQ_LIB_VERSION_STR.split('.')]
    assert ALSA_VERSION_LIST >= [1, 2, 4]
    ALSA_LIB_OK = True
except:
    ALSA_LIB_OK = False

from main_win import MainWindow
from patchance_pb_manager import PatchancePatchbayManager
from jack_manager import JackManager
if ALSA_LIB_OK:
    from alsa_manager import AlsaManager


@dataclass
class Main:
    app: QApplication
    main_win: MainWindow
    patchbay_manager: PatchancePatchbayManager
    jack_manager: JackManager
    alsa_manager: 'Optional[AlsaManager]'
    settings: QSettings


def signal_handler(sig, frame):
    if sig in (signal.SIGINT, signal.SIGTERM):
        QApplication.quit()

def get_code_root():
    return dirname(dirname(__file__))

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

    settings = QSettings()
    main_win = MainWindow()
    pb_manager = PatchancePatchbayManager(settings)
    jack_manager = JackManager(pb_manager)
    
    if ALSA_LIB_OK:
        alsa_manager = AlsaManager(pb_manager)
        if settings.value('Canvas/alsa_midi_enabled', False, type=bool):
            alsa_manager.add_all_ports()
    else:
        alsa_manager = None

    main = Main(app,
                main_win,
                pb_manager,
                jack_manager,
                alsa_manager,
                settings)

    pb_manager.finish_init(main)
    if not ALSA_LIB_OK:
        pb_manager.options_dialog.enable_alsa_midi(False)
    
    main_win.finish_init(main)
    main_win.show()

    app.exec()
    settings.sync()
    if alsa_manager is not None:
        alsa_manager.stop_events_loop()
    jack_manager.exit()
    pb_manager.save_positions()
    del app


if __name__ == '__main__':
    main_loop()
