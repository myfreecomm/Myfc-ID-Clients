# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.contrib.auth import views as auth_views

from shortcuts import route

urlpatterns = patterns('',
    url(r'^$', 'identity_client.views.sso_views.fetch_request_token', name='request_token'),
    url(r'^callback/$', 'identity_client.views.sso_views.fetch_access_token', name='callback'),

)
