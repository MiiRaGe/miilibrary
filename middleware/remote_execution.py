import os
import shlex
import subprocess
from time import sleep

import spur

from jsonrpc_requests import Server

from django.conf import settings
from paramiko import SSHException

from mii_common.tools import delete_dir


class ShellConnection(object):
    shell = None

    def connect(self):
        if settings.NAS_IP and settings.NAS_USERNAME and settings.REMOTE_FILE_OPERATION_ENABLED:
            print('Connecting')
            self.shell = spur.SshShell(
                hostname=settings.NAS_IP,
                username=settings.NAS_USERNAME,
                password=settings.NAS_PASSWORD,
                connect_timeout=3600,
                missing_host_key=spur.ssh.MissingHostKey.accept
            )

    def run(self, *args, **kwargs):
        if self.shell:
            max_retries = 2
            tries = 0
            while tries < max_retries:
                try:
                    result = self.shell.run(*args, **kwargs)
                    return result
                except SSHException:
                    self.connect()
                print('Connection lost, retrying')
                sleep(1)
            raise Exception('NAS unreachable')

    def is_connected(self):
        return self.shell is not None

shell_connection = ShellConnection()

shell_connection.connect()


def link(source_file, destination_file):
    # Source file is the destination of the link and destionation_file is the new link path
    if shell_connection.is_connected():
        result = shell_connection.run([u"ln", map_to_nas(source_file), map_to_nas(destination_file)])
        return result.return_code
    return os.link(source_file, destination_file)


def symlink(source_file, destination_file):
    # Source file is the destination of the link and destionation_file is the new link path
    if shell_connection.is_connected():
        result = shell_connection.run([u"ln", u"-s", map_to_nas(source_file), map_to_nas(destination_file)])
        return result.return_code
    return os.symlink(source_file, destination_file)


def unrar(source_file, destination_dir):
    # Source file is the archive file and destionation_dir is the extraction directory
    if shell_connection.is_connected():
        result = shell_connection.run(
            [settings.REMOTE_UNRAR_PATH, "e", "-y", map_to_nas(source_file), map_to_nas(destination_dir)])
        return result.return_code
    return subprocess.check_output(shlex.split('unrar e -y %s %s' % (source_file, destination_dir)))


def remove_dir(path):
    # This method is extremely dangerous as it will delete everything rm -rf
    if shell_connection.is_connected():
        result = shell_connection.run(["rm", "-rf", map_to_nas(path)])
        return result.return_code
    return delete_dir(path)


def map_to_nas(local_path):
    """
    This method maps between the files path mounted on the server executing the code, and the NAS on which the file are
    actually located.
    On the server, the folder can be mounted on /mnt/MoviesSeries
    But on the NAS the folder is actually /share/MD0_DATA/MoviesSeries, so if you want to do a symlink, you have to know
    The correct path on the NAS from the path you have with the mounted folder.
    You can have a smb server linked to you local filesystem to browse, remove, create dir, but you can't link file
    as you need knowledge on the actual filesystem which the nas does.
    :param local_path:
    :return:
    """
    return local_path.replace(settings.LOCAL_ROOT, settings.NAS_ROOT)


def remote_play(path):
    """
    This function remotes play a file to a kodi xbmc server.
    :param path:
    :return:
    """
    smb_path = path.format(destination_dir='smb://MIINAS/MoviesSeries')
    url = "http://192.168.0.149:8080/jsonrpc"
    http_client = Server(
        url,
        auth=(settings.JSON_RPC_USERNAME, settings.JSON_RPC_PASSWORD),
    )
    http_client.send_request('Player.Open', False, {'item': {'file': smb_path}})

