import errno
import logging
import os
import subprocess

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
    # lexists so that dangling symlinks are removed too
    if os.path.lexists(path):
        if os.path.islink(path):
            os.unlink(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)


class LibraryNotMounted(Exception):
    pass


def check_mounted(path):
    """
    Refuse to work on a missing or relative folder: an unset variable or a volume not mounted in the container would
    otherwise create an empty library in the working directory, or make every file in the db look deleted.
    """
    if not path or not os.path.isabs(path) or not os.path.isdir(path):
        raise LibraryNotMounted('%r is not an existing absolute folder, is the volume mounted?' % path)
    return path


def relative_symlink(target, link_path):
    # Relative links resolve the same on the NAS, inside containers and through NFS/SMB clients,
    # as long as both ends live in the same share.
    os.symlink(os.path.relpath(target, os.path.dirname(link_path)), link_path)


# errno values for which a hardlink can't be made but a copy can (other filesystem, protected_hardlinks...)
LINK_UNSUPPORTED_ERRNOS = (errno.EXDEV, errno.EPERM, errno.EMLINK, errno.EOPNOTSUPP)


def link_or_copy(source_file, destination_file, staging_dir):
    """
    Hardlink source_file to destination_file, or copy it when they are on different filesystems
    (e.g. torrents seeding on the NVMe volume and the library on the HDD volume).
    The copy is written in staging_dir first and renamed into place, so destination_file is never seen half
    written. staging_dir must be on the same filesystem as destination_file for the rename to be atomic.
    """
    try:
        os.link(source_file, destination_file)
        return
    except OSError as e:
        if e.errno not in LINK_UNSUPPORTED_ERRNOS:
            raise
    staging_file = os.path.join(make_dirs(staging_dir), os.path.basename(destination_file))
    shutil.copyfile(source_file, staging_file)
    os.replace(staging_file, destination_file)


def unrar(archive_file, destination_dir):
    return subprocess.check_output(['unrar', 'e', '-y', archive_file, os.path.join(destination_dir, '')])


def dict_apply(path, dictionnary, symlink_method=relative_symlink):
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
                        symlink_method(abs_path_to_name, new_one)
                    except OSError as e:
                        logger.error(u'Tried to symlink: "%s" to "%s/%s"' % (abs_path_to_name,
                                                                             current_path,
                                                                             name))
                        logger.error(u'Error: %s' % e)
                else:
                    current_path_content.remove(name)
                    if get_dir_size(abs_path_to_name) != get_dir_size(new_one):
                        safe_delete(new_one)
                        try:
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
