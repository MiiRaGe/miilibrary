import sys
# Then logic is base.py extends django.py and local.py needs to extends base.py
from base import *

if 'test' in sys.argv:
    from test import *
else:
    try:
        from local import *
    except ImportError:
        pass