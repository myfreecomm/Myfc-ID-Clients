from django.conf.urls.defaults import *

urlpatterns = patterns('django.views.generic.simple',
    url(r'^index.php$',
        'direct_to_template', {'template': 'iframe.html'},
        name='iframe'
    ),
)

urlpatterns += patterns('',
     (r'^accounts/', include('identity_client.urls')),
     (r'^client-app/', include('example_app.urls')),
     (r'^sso/', include('identity_client.sso_urls', namespace='sso_consumer')),
     (r'$', 'django.views.generic.simple.redirect_to', {'url': '/client-app/profile/'}),
)
