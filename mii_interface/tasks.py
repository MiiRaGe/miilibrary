from __future__ import absolute_import

import time

from datetime import timedelta
from django.utils import timezone

from celery import shared_task

from mii_interface.models import Report
from mii_rss.models import FeedEntries
from mii_rss.tasks import send_to_transmission_with_retry
from mii_sorter.models import WhatsNew
from mii_unpacker.models import Unpacked


@shared_task(serializer='json')
def clean_history():
    month_old = timezone.now() - timedelta(days=45)
    FeedEntries.objects.filter(date__lte=month_old).delete()
    WhatsNew.objects.filter(date__lte=month_old).delete()
    Report.objects.filter(date__lte=month_old).delete()

    parameters = {
        "method": "torrent-get",
        "arguments": {
            "fields": ["addedDate", "id"]
        }
    }
    response = send_to_transmission_with_retry(parameters)
    if not response:
        return
    id_date_list = response['arguments']['torrents']
    ids_to_remove = []
    three_month_ago = time.time() - (60 * 60 * 24 * 90)
    for element in id_date_list:
        if element['addedDate'] <= three_month_ago:
            ids_to_remove.append(element['id'])

    parameters = {
        "method": "torrent-remove",
        "arguments": {
            "ids": ids_to_remove,
            "delete-local-data": True
        }
    }
    response = send_to_transmission_with_retry(parameters)
    if not response:
        return
    four_month_ago = timezone.now() - timedelta(days=120)
    Unpacked.objects.filter(timestamp__lte=four_month_ago).delete()