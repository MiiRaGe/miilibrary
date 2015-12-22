from __future__ import absolute_import

import requests

from celery import task
from django.conf import settings

from middleware.decorators import single_instance_task
from mii_sorter.logic import Sorter


@task(serializer='json')
@single_instance_task(60*30)
def sort():
    sorter = Sorter()
    sorter.sort()


@task(serializer='json')
def rescan_media_streamer():
    requests.get(settings.MEDIA_RENDERER_RESCAN_URL)