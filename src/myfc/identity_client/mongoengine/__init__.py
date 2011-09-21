# -*- coding: utf-8 -*-
from django.conf import settings

import mongoengine

mongoengine.connect(
    settings.NOSQL_DATABASES['NAME'],
    host=settings.NOSQL_DATABASES['HOST']
)
