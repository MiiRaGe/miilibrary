import commands
import logging
import os
import shutil
import subprocess

logger = logging.getLogger(__name__)


# Create the directory @param(path) and return the path after creation [Error safe]
def make_dir(path):
    # Avoid the raise of IOError exception by checking if the directory exists first
    try:
        os.mkdir(path)
    except OSError as e:
        if e.errno != 17:
            logger.warning(u'Exception in make_dir(%s): %s' % (e.filename, repr(e)))
    return path


# Create the directorise @param(path) and return the directory_path after creation [Error safe]
def make_dirs(path):
    # Avoid the raise of IOError exception by checking if the directory exists first
    path += os.sep
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != 17:
            logger.warning(u'Exception in make_dir(%s): %s' % (e.filename, repr(e)))
    return path


def delete_dir(path, include_root=True):
    """deletes the path entirely"""
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    if include_root:
        os.rmdir(path)


def listdir_abs(parent):
    return [os.path.join(parent, child) for child in os.listdir(parent)]


def dict_apply(path, dictionnary, symlink_method=None):
    '''
    This method expect a dict with any depth where leaf are a list of tuple (name, path) where a symlink is going to be created
    following the path in the tree to match the patch in the file system.
    {'a': {'b': {'c': [('a', '/path_to/a')]}}} is going to create path/a/b/c/a (where a is a symlink to /path_to/a)
    :param dictionnary:
    :return:
    '''
    if not dictionnary:
        return
    for root, leaf in dictionnary.items():
        if not leaf:
            continue

        current_path = make_dir(os.path.join(path, root))
        if isinstance(leaf, list):
            for name, abs_path_to_name in leaf:
                try:
                    if not symlink_method:
                        os.symlink(abs_path_to_name, os.path.join(current_path, name))
                    else:
                        symlink_method(abs_path_to_name, os.path.join(current_path, name))
                except OSError as e:
                    logger.error(u'Tried to symlink: "%s" to "%s/%s"' % (abs_path_to_name,
                                                                        current_path,
                                                                        name))
                    logger.error(u'Error: %s' % e)
        else:
            dict_apply(current_path, leaf, symlink_method=symlink_method)
