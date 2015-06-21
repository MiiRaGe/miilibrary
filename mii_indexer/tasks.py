from __future__ import absolute_import

import os

from celery import task

from django.conf import settings

from mii_indexer.indexer import Indexer


@task
def index_movies():
    indexer = Indexer()
    indexer.index()