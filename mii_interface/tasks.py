import requests

from mii_celery import app
from mii_unpacker.tasks import unpack
from mii_sorter.tasks import sort
from mii_indexer.tasks import index_movies

@app.task()
def unpack_sort_index():
    unpack()
    sort()
    index_movies()
    requests.get('http://192.168..0.2:9000/rpc/rescan')