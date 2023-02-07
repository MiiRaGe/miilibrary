import pytz


from datetime import datetime
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyDateTime, FuzzyChoice

from mii_interface.models import Report


class ReportFactory(DjangoModelFactory):
    class Meta:
        model = Report

    date = FuzzyDateTime(datetime(2000, 1, 1, tzinfo=pytz.UTC))
    report_type = FuzzyChoice(['sorter', 'indexer', 'unpacker', 'rss'])
    report_html = '<p>Report<p>'
