# -*- coding: utf-8 -*-
import mongoengine

from django.conf import settings as django_settings
from django.test.simple import TestCase as SimpleTestCase

import models
import settings

__all__ = ['models', 'settings', 'TestCase']


mongoengine.connect(
    django_settings.NOSQL_DATABASES['NAME'],
    host=django_settings.NOSQL_DATABASES['HOST']
)


class TestCase(SimpleTestCase):
    """
    TestCase class that clear the collection between the tests
    """
    def __init__(self, methodName='runtest'):
        self.db = mongoengine.connection._get_db()
        super(TestCase, self).__init__(methodName)

    def _post_teardown(self):
        super(TestCase, self)._post_teardown()
        for collection in self.db.collection_names():
            if collection == 'system.indexes':
                continue
            self.db.drop_collection(collection)
