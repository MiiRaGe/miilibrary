from __future__ import absolute_import

from celery import task

from django.conf import settings

from mii_sorter.sorter import Sorter

from django.core.cache import cache
lock_id = "indexer"
lock_expire = 3600

acquire_lock = lambda: cache.add(lock_id, "indexing", lock_expire)
get_lock = lambda: cache.get(lock_id)
release_lock = lambda: cache.delete(lock_id)


@task
def sort():
    if get_lock():
        return
    acquire_lock()
    sorter = Sorter()
    sorter.sort()
    release_lock()