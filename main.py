import sys
import tools

from miinaslibrary import MiiNASLibrary

if __name__ == '__main__':
    if tools.validate_settings():
        mnl = MiiNASLibrary()
        mnl.run(sort_only='-s' in sys.argv, index_only='-i' in sys.argv)
    else:
        print "Invalid settings in settings/base.py or settings/local.py"
