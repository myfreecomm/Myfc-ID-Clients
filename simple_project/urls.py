from django.conf.urls.defaults import *

urlpatterns = patterns('',
     (r'^accounts/', include('identity_auth_client.urls')),
     (r'^accounts/', include('identity_registration_client.urls')),
     #(r'$', 'django.views.generic.simple.redirect_to', {'url': '/accounts/login/'}),
)
