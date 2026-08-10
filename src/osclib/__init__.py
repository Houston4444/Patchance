from typing import TYPE_CHECKING

LIBLO_EXISTS = True

if TYPE_CHECKING:
    from dum_imports import (
        UDP, UNIX, TCP, Message, Bundle, Address, Server, ServerThread,
        ServerError, AddressError, make_method, send)
else:
    # Do not remove any imports here !!!
    try:
        from liblo import (
            UDP, UNIX, TCP, Message, Bundle, Address, Server, ServerThread,
            ServerError, AddressError, make_method, send)
    except ImportError:
        try:
            from pyliblo3 import (
                UDP, UNIX, TCP, Message, Bundle, Address, Server, ServerThread,
                ServerError, AddressError, make_method, send)
        except ImportError:
            LIBLO_EXISTS = False
            _logger.warning(
                'Failed to find a liblo lib for OSC (liblo or pyliblo3)')
            _logger.warning(str(e))