from django.utils import timezone
from django.db.models import Model, CharField, TextField, DateTimeField


class Report(Model):
    date = DateTimeField(default=timezone.now, db_index=True)
    report_type = CharField(max_length=50, db_index=True)
    report_html = TextField()
