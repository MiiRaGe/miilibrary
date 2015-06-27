from __future__ import absolute_import

import os

from celery import task

from django.conf import settings

from mii_common import tools
from mii_unpacker.unpacker import RecursiveUnrarer

from django.core.cache import cache
lock_id = "unpacker"
lock_expire = 3600

acquire_lock = lambda: cache.add(lock_id, "unpacking", lock_expire)
get_lock = lambda: cache.get(lock_id)
release_lock = lambda: cache.delete(lock_id)

@task
def unpack():
    if get_lock():
        return
    acquire_lock()
    output_dir = settings.DESTINATION_FOLDER
    data_dir = tools.make_dir(os.path.join(output_dir, 'data'))
    unpacker = RecursiveUnrarer(settings.SOURCE_FOLDER, data_dir)
    unpacker.unrar_and_link()
    unpacker.cleanup()
    unpacker.print_statistic()
    release_lock()