# Import the configuration settings file - REPLACE projectname with your project
config_module = __import__('settings.base', globals(), locals(), 'base')

# Load the config settings properties into the local scope.
for setting in dir(config_module):
    if setting == setting.upper():
        locals()[setting] = getattr(config_module, setting)


from settings.base import DATABASES


DATABASES['default'] = {
    'USER': 'root',
    'HOST': '127.0.0.1',
    'ENGINE': 'django.db.backends.mysql',
    'NAME': 'testdb'
}

REMOTE_FILE_OPERATION_ENABLED = False