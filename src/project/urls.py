# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('django.views.generic.simple',
    url(r'^index.php$',
        'direct_to_template', {'template': 'iframe.html'},
        name='iframe'
    ),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve',
            { 'document_root': settings.MEDIA_ROOT }),
    )


urlpatterns += patterns('',
     (r'^accounts/', include('identity_client.urls')),
     (r'^client-app/', include('example_app.urls')),
     (r'^sso/', include('identity_client.sso.urls', namespace='sso_consumer')),
     (r'$', 'django.views.generic.simple.redirect_to', {'url': '/client-app/profile/'}),
)
