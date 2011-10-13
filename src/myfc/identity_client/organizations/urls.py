# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('identity_client.organizations.views',
    url(r'^$', 'list_accounts', name='list_accounts'),
)
