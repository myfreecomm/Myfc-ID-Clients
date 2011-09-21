# -*- coding: utf-8 -*-
import mongoengine

from django.conf import settings
from django.test.simple import TestCase as SimpleTestCase

import models

__all__ = ['models', 'TestCase']

mongoengine.connect(
    settings.NOSQL_DATABASES['NAME'],
    host=settings.NOSQL_DATABASES['HOST']
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

