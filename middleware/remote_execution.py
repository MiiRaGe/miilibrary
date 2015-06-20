import os
import subprocess
import spur

from django.conf import settings

shell = None
if settings.NAS_IP and settings.NAS_USERNAME and settings.REMOTE_FILE_OPERATION_ENABLED:
    shell = spur.SshShell(hostname=settings.NAS_IP, username=settings.NAS_USERNAME, connect_timeout=2400)


def link(source_file, destination_file):
    # Source file is the destination of the link and destionation_file is the new link path
    if shell:
        result = shell.run(["ln", map_to_nas(source_file), map_to_nas(destination_file)])
        return result.return_code
    return os.link(source_file, destination_file)


def symlink(source_file, destination_file):
    # Source file is the destination of the link and destionation_file is the new link path
    if shell:
        result = shell.run(["ln", "-s", map_to_nas(source_file), map_to_nas(destination_file)])
        return result.return_code
    return os.symlink(source_file, destination_file)


def unrar(source_file, destination_dir):
    # Source file is the archive file and destionation_dir is the extraction directory
    if shell:
        result = shell.run(["/usr/local/sbin/unrar", "e", "-y", map_to_nas(source_file), map_to_nas(destination_dir)])
        return result.return_code
    return subprocess.check_output('unrar e -y %s %s' % (source_file, destination_dir))


def map_to_nas(local_path):
    '''
    This method maps between the compute executing the code, and the NAS on which the file are actually located.
    You can have a smb server linked to you local filesystem to browse, remove, create dir, but you can't link file
    as you need knowledge on the actual filesystem which the nas does.
    :param local_path:
    :return:
    '''
    return local_path.replace(settings.LOCAL_ROOT, settings.NAS_ROOT)