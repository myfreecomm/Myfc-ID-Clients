# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.contrib.auth import views as auth_views

from views import login as client_login
from forms import IdentityAuthenticationForm 

urlpatterns = patterns('',
                   url(r'^login/$',
                       client_login,
                       {'template_name': 'login.html',
                        'authentication_form': IdentityAuthenticationForm},
                       name='auth_login'),
                   url(r'^logout/$',
                       auth_views.logout_then_login,
                       name='auth_logout'),
)
