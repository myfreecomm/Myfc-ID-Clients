from django.conf.urls.defaults import *

urlpatterns = patterns('',
     (r'^accounts/', include('identity_client.urls')),
     (r'^client-app/', include('example_app.urls')),
     (r'$', 'django.views.generic.simple.redirect_to', {'url': '/client-app/profile/'}),
)
