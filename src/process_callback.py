from ctypes import CDLL, c_ulong, c_void_p, c_int
from pathlib import Path

ccb = CDLL(str(Path(__file__).parent / 'process_cb.so'))

process_cb = ccb.process_cb
process_cb.argtypes = [c_ulong, c_void_p]
process_cb.restype = c_int
