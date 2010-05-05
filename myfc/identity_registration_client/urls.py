from django.conf.urls.defaults import *
from shortcuts import route
from identity_registration_client.views import register_identity, new_identity

urlpatterns = patterns('',
     route(r'^registration/',
            POST=register_identity,
            GET= new_identity,
            name='register_account'),
)