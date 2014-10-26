import tools

from miinaslibrary import MiiNASLibrary


def main_wait():
    mnl = MiiNASLibrary()
    mnl.run()

if __name__ == '__main__':
    if tools.validate_settings():
        main_wait()
    else:
        print "Invalid settings in settings/base.py or settings/local.py"
