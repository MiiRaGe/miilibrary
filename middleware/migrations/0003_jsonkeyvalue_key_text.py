# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('middleware', '0002_auto_20150708_2207'),
    ]

    operations = [
        migrations.AddField(
            model_name='jsonkeyvalue',
            name='key_text',
            field=models.CharField(default=b'', max_length=200),
        ),
    ]
