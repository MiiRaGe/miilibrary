from __future__ import absolute_import

import os

from celery import task

from django.conf import settings

from mii_indexer.indexer import Indexer

from django.core.cache import cache
lock_id = "indexer"
lock_expire = 3600

acquire_lock = lambda: cache.add(lock_id, "indexing", lock_expire)
get_lock = lambda: cache.get(lock_id)
release_lock = lambda: cache.delete(lock_id)

@task
def index_movies():
    if get_lock():
        return
    acquire_lock()
    indexer = Indexer()
    indexer.index()
    release_lock()