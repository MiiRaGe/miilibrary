from __future__ import absolute_import

from celery import shared_task
from dbbackup.management.commands.dbbackup import Command


@shared_task(serializer='json')
def db_backup():
    Command().handle(verbosity=1, clean=True, compress=True)
