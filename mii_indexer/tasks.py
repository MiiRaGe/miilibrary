import os

from django.conf import settings
from celery import app

from mii_indexer.indexer import Indexer


@app.task()
def index_movies():
    indexer = Indexer(os.path.join(settings.DESTINATION_FOLDER, 'Movies'))
    indexer.index()