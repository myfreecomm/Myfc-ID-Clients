from django.conf.urls.defaults import *

urlpatterns = patterns('',
     (r'^accounts/', include('identity_auth_client.urls')),
     (r'^accounts/', include('identity_registration_client.urls')),
)
