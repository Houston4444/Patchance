import logging

from qtpy.QtCore import QObject

from patch_engine import PatchEngine


_logger = logging.getLogger(__name__)


class PatchTimeoutObj(QObject):
    def __init__(self, patch_engine: PatchEngine):
        super().__init__()
        self.pe = patch_engine
        self.n = 0
        
    def check_patch(self):
        pe = self.pe
        n = self.n

        if pe.jack_running:
            if n % 4 == 0:
                pe.remember_dsp_load()
                if pe.dsp_wanted and n % 20 == 0:
                    pe.send_dsp_load()

            pe.process_patch_events()
            pe.check_pretty_names_export()
            pe.send_transport_pos()
            
        else:
            if n % 10 == 0:
                if pe.client is not None:
                    _logger.debug(
                        'deactivate JACK client after server shutdown')
                    pe.client.deactivate()
                    _logger.debug('close JACK client after server shutdown')
                    pe.client.close()
                    _logger.debug('close JACK client done')
                    pe.client = None
                _logger.debug('try to start JACK')
                pe.start_jack_client()
        
        self.n += 1
        
        # for faster modulos
        if n == 20:
            n = 0