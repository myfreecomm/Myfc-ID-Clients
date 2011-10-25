# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.contrib.auth import views as auth_views

from shortcuts import route
from views.client_views import login, show_login
from views.client_views import new_identity, register
from api import AccountActivationView
from forms import IdentityAuthenticationForm, RegistrationForm

urlpatterns = patterns('',
    route(r'^login/$',
        GET=show_login,
        POST=login,
        kwargs={'authentication_form': IdentityAuthenticationForm},
        name='auth_login'
    ),
    route(r'^registration/',
        GET=new_identity,
        POST=register,
        kwargs={'registration_form': RegistrationForm},
        name='registration_register'
    ),
     url(r'^logout/$',
        auth_views.logout,
        {'template_name': 'logout.html'},
        name='auth_logout'
    ),
    url(r'^(?P<uuid>(\w{8}-\w{4}-\w{4}-\w{4}-\w{12}){1})/$',
        AccountActivationView.as_view(),
        name='account_activation'
    ),
)
