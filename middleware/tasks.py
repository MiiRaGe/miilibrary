from __future__ import absolute_import

from celery import task
from dbbackup.management.commands.dbbackup import Command


@task(serializer='json')
def db_backup():
    Command().handle(verbosity=1, clean=True, compress=True)
