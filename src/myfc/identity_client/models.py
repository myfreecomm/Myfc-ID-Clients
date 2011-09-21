# -*- coding: utf-8 -*-
from django.conf import settings

__all__ = ['Identity']

module_name = 'identity_client.%s' % settings.PERSISTENCE_STRATEGY

models = __import__(
    '%s.models' % module_name, 
    fromlist=[module_name]
)

Identity = models.Identity
