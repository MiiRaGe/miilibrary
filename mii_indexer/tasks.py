from __future__ import absolute_import

from celery import task
from middleware.decorators import single_instance_task

from mii_indexer.logic import Indexer


@task(serializer='json')
@single_instance_task(60*30)
def index_movies():
    indexer = Indexer()
    indexer.index()
