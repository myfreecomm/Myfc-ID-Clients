# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.contrib.auth import views as auth_views

from views import profile

urlpatterns = patterns('',
                   url(r'^profile/$',
                       profile,
                       {'template_name': 'profile.html'},
                       name='user_profile'),
)
