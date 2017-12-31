import logging
import os
from errno import ENOTDIR

import shutil

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


def get_size(file_name):
    return os.path.getsize(os.path.abspath(file_name))


def get_dir_size(dir_name):
    # TODO : Write unite test for that method
    return sum([get_size(os.path.join(dir_name, x)) for x in os.listdir(dir_name)]) if os.path.exists(dir_name) else 0


def safe_delete(path):
    if os.path.exists(path):
        if os.path.islink(path):
            os.unlink(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)


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
    path_content = set(os.listdir(path))
    dictionarry_keys = set(dictionnary.keys())
    to_remove = path_content - dictionarry_keys
    for remove in to_remove:
        full_remove = os.path.join(path, remove)
        safe_delete(full_remove)

    for root, leaf in dictionnary.items():
        full_leaf = os.path.join(path, root)
        if not leaf:
            safe_delete(full_leaf)
            continue
        current_path = make_dir(os.path.join(path, root))
        current_path_content = set(os.listdir(current_path))
        if isinstance(leaf, list):
            for name, abs_path_to_name in leaf:
                new_one = os.path.join(current_path, name)
                if name not in current_path_content:
                    try:
                        if not symlink_method:
                            os.symlink(abs_path_to_name, new_one)
                        else:
                            symlink_method(abs_path_to_name, new_one)
                    except OSError as e:
                        logger.error(u'Tried to symlink: "%s" to "%s/%s"' % (abs_path_to_name,
                                                                             current_path,
                                                                             name))
                        logger.error(u'Error: %s' % e)
                else:
                    current_path_content = current_path_content.remove(name)
                    if get_dir_size(abs_path_to_name) != get_dir_size(new_one):
                        safe_delete(new_one)
                        try:
                            if not symlink_method:
                                os.symlink(abs_path_to_name, new_one)
                            else:
                                symlink_method(abs_path_to_name, new_one)
                        except OSError as e:
                            logger.error(u'Tried to symlink: "%s" to "%s/%s"' % (abs_path_to_name,
                                                                                 current_path,
                                                                                 name))
                            logger.error(u'Error: %s' % e)
            if current_path_content:
                for content in current_path_content:
                    full_content = os.path.join(current_path, content)
                    safe_delete(full_content)

        else:
            dict_apply(current_path, leaf, symlink_method=symlink_method)
