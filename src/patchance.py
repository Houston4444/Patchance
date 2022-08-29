#!/usr/bin/python3 -u

APP_TITLE = 'Patchance'
VERSION = (0, 1, 0)

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


import signal
import logging

from dataclasses import dataclass
from os.path import dirname

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon, QFontDatabase
from PyQt5.QtCore import QLocale, QTranslator, QTimer, QLibraryInfo, QSettings

from main_win import MainWindow
from patchance_pb_manager import PatchancePatchbayManager
from jack_manager import JackManager


@dataclass
class Main:
    app: QApplication
    main_win: MainWindow
    patchbay_manager: PatchancePatchbayManager
    jack_manager: JackManager
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

    main = Main(app, main_win, pb_manager, jack_manager, settings)
    pb_manager.finish_init(main)
    main_win.finish_init(main)
    main_win.show()

    app.exec()
    settings.sync()
    jack_manager.exit()
    pb_manager.save_positions()
    del app


if __name__ == '__main__':
    main_loop()
