from django.db.models import Model, CharField, TextField, DateField


class Report(Model):
    date = DateField()
    report_type = CharField(max_length=50, db_index=True)
    report_html = TextField()