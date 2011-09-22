# -*- coding: utf-8 -*-
from django.conf import settings

__all__ = ['PERSISTENCE_MODULE']

module_name = 'identity_client.%s' % settings.PERSISTENCE_STRATEGY

PERSISTENCE_MODULE = __import__(
    module_name,
    fromlist=['identity_client']
)

new_settings = getattr(PERSISTENCE_MODULE, 'settings')
for attr_name in dir(new_settings):
    if not attr_name.isupper():
        continue

    attr_value = getattr(new_settings, attr_name)
    setattr(settings, attr_name, attr_value)
