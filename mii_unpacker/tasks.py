from __future__ import absolute_import

import os

from celery import task

from django.conf import settings

from mii_common import tools
from mii_unpacker.unpacker import RecursiveUnrarer


@task
def unpack():
    output_dir = settings.DESTINATION_FOLDER
    data_dir = tools.make_dir(os.path.join(output_dir, 'data'))
    unpacker = RecursiveUnrarer(settings.SOURCE_FOLDER, data_dir)
    unpacker.unrar_and_link()
    unpacker.cleanup()
    unpacker.print_statistic()