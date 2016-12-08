import sys
# Then logic is base.py extends django.py and local.py needs to extends base.py
# Import the configuration settings file - REPLACE projectname with your project
config_module = __import__('settings.base', globals(), locals(), 'base')

# Load the config settings properties into the local scope.
for setting in dir(config_module):
    if setting == setting.upper():
        locals()[setting] = getattr(config_module, setting)

if 'test' in sys.argv:
    config_module = __import__('settings.test', globals(), locals(), 'test')

    # Load the config settings properties into the local scope.
    for setting in dir(config_module):
        if setting == setting.upper():
            locals()[setting] = getattr(config_module, setting)
else:
    try:
        config_module = __import__('settings.local', globals(), locals(), 'local')

        # Load the config settings properties into the local scope.
        for setting in dir(config_module):
            if setting == setting.upper():
                locals()[setting] = getattr(config_module, setting)

    except ImportError:
        pass