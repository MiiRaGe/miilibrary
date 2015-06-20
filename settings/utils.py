import os.path


PROJECT_ROOT = os.path.normpath(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), os.pardir)))


def relative(*args):
    return os.path.join(PROJECT_ROOT, *args)