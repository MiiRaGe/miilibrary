# Import the configuration settings file - REPLACE projectname with your project
config_module = __import__('settings.base', globals(), locals(), 'base')

# Load the config settings properties into the local scope.
for setting in dir(config_module):
    if setting == setting.upper():
        locals()[setting] = getattr(config_module, setting)


from settings.base import DATABASES


DATABASES['default'] = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': 'test_db.db'
}

REMOTE_FILE_OPERATION_ENABLED = False