from __future__ import absolute_import

from celery import shared_task
from middleware.decorators import single_instance_task

from mii_indexer.logic import Indexer


@shared_task(serializer='json')
@single_instance_task(60*30)
def index_movies():
    indexer = Indexer()
    indexer.index()
