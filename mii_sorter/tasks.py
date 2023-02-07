from __future__ import absolute_import

import requests

from celery import shared_task
from django.conf import settings

from middleware.decorators import single_instance_task
from mii_sorter.logic import Sorter


@shared_task(serializer='json')
@single_instance_task(60*30)
def sort():
    sorter = Sorter()
    sorter.sort()