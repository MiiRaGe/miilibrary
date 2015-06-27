from __future__ import absolute_import

from celery import task

from middleware.decorators import single_instance_task

from mii_sorter.sorter import Sorter


@task
@single_instance_task(60*30)
def sort():
    sorter = Sorter()
    sorter.sort()

