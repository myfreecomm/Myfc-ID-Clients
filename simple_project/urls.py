from django.conf.urls.defaults import *

urlpatterns = patterns('',
     (r'^accounts/', include('identity_client.urls')),
     (r'^client-app/', include('example_app.urls')),
     (r'^sso-sample/', include('sso_consumer.urls', namespace='sso_consumer')),
     (r'$', 'django.views.generic.simple.redirect_to', {'url': '/client-app/profile/'}),
)
