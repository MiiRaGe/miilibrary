import sys
# Then logic is base.py extends django.py and local.py needs to extends base.py
try:
    from local import *
except ImportError:
    pass

if 'test' in sys.argv:
    from test import *
