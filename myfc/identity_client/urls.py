# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.contrib.auth import views as auth_views

from shortcuts import route
from views.registration import register_identity, new_identity
from views.auth import login as client_login
from forms import IdentityAuthenticationForm 

urlpatterns = patterns('',
            url(r'^login/$',
                client_login,
                {'template_name': 'login.html',
                'authentication_form': IdentityAuthenticationForm},
                name='auth_login'
            ),
            url(r'^logout/$',
                auth_views.logout_then_login,
                name='auth_logout'
            ),
            route(r'^registration/',
                POST=register_identity,
                GET= new_identity,
                name='registration_register'
            ),
)
