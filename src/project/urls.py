# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('django.views.generic.simple',
    url(r'^$',
        'direct_to_template', {'template': 'index.html'},
        name='index'
    ),
)

urlpatterns += patterns('',
     (r'^accounts/', include('identity_client.urls')),
     (r'^developer/', include('developer.urls')),
     (r'^sso/', include('identity_client.sso.urls', namespace='sso_consumer')),
)

urlpatterns += patterns('identity_client.views.client_views',
     url(r'^organizations/$', 'list_accounts', name='list_accounts'),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve',
            { 'document_root': settings.MEDIA_ROOT }),
    )
