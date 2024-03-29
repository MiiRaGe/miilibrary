from __future__ import absolute_import

from celery import shared_task
from middleware.decorators import single_instance_task
from middleware.remote_execution import shell_connection

from mii_indexer.logic import Indexer


@shared_task(serializer='json')
@single_instance_task(60*30)
def index_movies():
    indexer = Indexer()
    indexer.index()


@shared_task(serializer='json')
@single_instance_task(60*30)
def apply_local_index():
    if shell_connection.is_connected():
        # Make it more generic... Or wait for the object server
        shell_connection.run([u"python", u"/share/MD0_DATA/miilibrary/apply_index_local.py"])
