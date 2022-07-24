 
#!/usr/bin/python3 -u

#libs
from dataclasses import dataclass
import signal
import sys
import time
import logging

from os.path import dirname

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon, QFontDatabase
from PyQt5.QtCore import QLocale, QTranslator, QTimer, QLibraryInfo, QSettings

from src.main_win import MainWindow
from src.patchance_pb_manager import PatchancePatchbayManager
from src.jack_manager import JackManager


def signal_handler(sig, frame):
    if sig in (signal.SIGINT, signal.SIGTERM):
        QApplication.quit()

def get_code_root():
    return dirname(__file__)

def make_logger():
    logger = logging.getLogger(__name__)
    log_handler = logging.StreamHandler()
    log_handler.setFormatter(logging.Formatter(
        f"%(name)s - %(levelname)s - %(message)s"))
    logger.setLevel(logging.WARNING)
    logger.addHandler(log_handler)

@dataclass
class Main:
    app: QApplication
    main_win: MainWindow
    patchbay_manager: PatchancePatchbayManager
    settings: QSettings


if __name__ == '__main__':
    # set Qt Application
    APP_TITLE = 'Patchance'
    
    make_logger()
    
    app = QApplication(sys.argv)
    app.setApplicationName(APP_TITLE)
    # app.setApplicationVersion(ray.VERSION)
    app.setOrganizationName(APP_TITLE)
    # app.setWindowIcon(QIcon(
    #     f':main_icon/scalable/{ray.APP_TITLE.lower()}.svg'))
    # app.setQuitOnLastWindowClosed(False)
    # app.setDesktopFileName(ray.APP_TITLE.lower())

    ### Translation process
    locale = QLocale.system().name()

    app_translator = QTranslator()
    if app_translator.load(QLocale(), APP_TITLE.lower(),
                           '_', "%s/locale" % get_code_root()):
        app.installTranslator(app_translator)

    print('lmmdlld',"%s/HoustonPatchbay/locale" % get_code_root() )

    patchbay_translator = QTranslator()
    if patchbay_translator.load(QLocale(), 'patchbay',
                                '_', "%s/HoustonPatchbay/locale" % get_code_root()):
        app.installTranslator(patchbay_translator)

    sys_translator = QTranslator()
    path_sys_translations = QLibraryInfo.location(QLibraryInfo.TranslationsPath)
    if sys_translator.load(QLocale(), 'qt', '_', path_sys_translations):
        app.installTranslator(sys_translator)

    QFontDatabase.addApplicationFont(":/fonts/Ubuntu-R.ttf")
    QFontDatabase.addApplicationFont(":fonts/Ubuntu-C.ttf")

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
    
    main = Main(app, main_win, pb_manager, settings)
    pb_manager.finish_init(main)
    main_win.finish_init(main)
    
    jack_manager = JackManager(pb_manager)
    
    main_win.show()

    app.exec()

    del app
