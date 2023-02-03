"""Addon for Candle Controller."""

# You will need to change the name in this file in two places, marked below:

from os import path
import functools
import signal
import sys
import time

sys.path.append(path.join(path.dirname(path.abspath(__file__)), 'lib'))

# Change this to reflect your addon's adapter class. It should be the same as the name in the:
from pkg.matter_adapter import MatterAdapter  # noqa


_DEBUG = False
_ADAPTER = None

print = functools.partial(print, flush=True)


def cleanup(signum, frame):
    """Clean up any resources before exiting."""
    if _ADAPTER is not None:
        _ADAPTER.close_proxy()

    sys.exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    # Change this to the correct name too:
    _ADAPTER = MatterAdapter(verbose=_DEBUG)
    
    # Wait until the proxy stops running, indicating that the gateway shut us
    # down.
    while _ADAPTER.proxy_running():
        time.sleep(2)
