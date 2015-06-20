from __future__ import absolute_import

from celery import task

from django.conf import settings

from mii_sorter.sorter import Sorter


@task
def sort():
    sorter = Sorter()
    sorter.sort()