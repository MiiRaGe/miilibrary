from __future__ import absolute_import

import os
from time import sleep

from celery import task

from django.conf import settings
from middleware.decorators import single_instance_task

from mii_common import tools
from mii_unpacker.logic import RecursiveUnrarer


@task(serializer='json')
@single_instance_task(60*60)
def unpack():
    unpacker = RecursiveUnrarer()
    unpacker.unrar_and_link()
    unpacker.cleanup()
    unpacker.print_statistic()
