# -*- coding: utf-8 -*-
from django.conf import settings

__all__ = ['PERSISTENCE_MODULE']

module_name = 'identity_client.%s' % settings.PERSISTENCE_STRATEGY

PERSISTENCE_MODULE = __import__(
    module_name,
    fromlist=['identity_client']
)
