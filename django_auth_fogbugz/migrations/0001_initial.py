# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='FogBugzProfile',
            fields=[
                ('user', models.OneToOneField(primary_key=True, to=settings.AUTH_USER_MODEL, serialize=False)),
                ('token', models.CharField(blank=True, max_length=32, default='')),
                ('ixPerson', models.PositiveIntegerField()),
                ('is_normal', models.BooleanField()),
                ('is_community', models.BooleanField()),
                ('is_administrator', models.BooleanField()),
            ],
        ),
    ]
