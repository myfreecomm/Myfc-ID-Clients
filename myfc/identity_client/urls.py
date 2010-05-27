# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.contrib.auth import views as auth_views

from shortcuts import route
from views import login, show_login
from views import new_identity, register 
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
                auth_views.logout_then_login,
                name='auth_logout'
            ),
)
