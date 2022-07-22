
from os.path import dirname

def get_code_root() -> str:
    return dirname(dirname((__file__)))