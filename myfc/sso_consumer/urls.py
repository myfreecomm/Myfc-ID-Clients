# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.contrib.auth import views as auth_views

from shortcuts import route

urlpatterns = patterns('',
    url(r'^$', 'sso_consumer.views.request_token', name='request_token'),
    url(r'^callback/$', 'sso_consumer.views.callback', name='callback'),

)
