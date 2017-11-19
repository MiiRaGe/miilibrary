from __future__ import absolute_import

from datetime import timedelta
from django.utils import timezone

from celery import task

from mii_interface.models import Report
from mii_rss.models import, FeedEntries
from mii_sorter.models import WhatsNew


@task(serializer='json')
def clean_history():
    month_old = timezone.now() - timedelta(days=45)
    FeedEntries.objects.filter(date__lte=month_old).delete()
    WhatsNew.objects.filter(date__lte=month_old).delete()
    Report.objects.filter(date__lte=month_old).delete()