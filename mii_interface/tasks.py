from mii_celery import app
from mii_unpacker.tasks import unpack
from mii_sorter.tasks import sort
from mii_indexer.tasks import index_movies

@app.task()
def unpack_sort_index():
    unpack()
    sort()
    index_movies()