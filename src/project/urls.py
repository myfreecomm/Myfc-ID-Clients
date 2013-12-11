# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.conf import settings
from django.views.generic import TemplateView

urlpatterns = patterns('',
    url(r'^$',
        TemplateView.as_view(template_name = 'index.html'),
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
