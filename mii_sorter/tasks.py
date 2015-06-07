from celery import app
from django.conf import settings

from mii_sorter.sorter import Sorter


@app.task()
def sort():
    sorter = Sorter(settings.DESTINATION_FOLDER)
    sorter.sort()