# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.contrib.auth import views as auth_views

from shortcuts import route
from views import simple_login, login_or_register, register_identity
from forms import IdentityAuthenticationForm 

urlpatterns = patterns('',
            url(r'^simple-login/$',
                simple_login,
                {'authentication_form': IdentityAuthenticationForm},
                name='auth_simple_login'
            ),
            url(r'^login/$',
                login_or_register,
                name='auth_login'
            ),
            url(r'^logout/$',
                auth_views.logout_then_login,
                name='auth_logout'
            ),
            url(r'^registration/',
                register_identity,
                name='registration_register'
            ),
)
