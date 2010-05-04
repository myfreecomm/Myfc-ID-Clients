from django.conf import settings
from django.conf.urls.defaults import *

urlpatterns = patterns('',
    # Uncomment the next line to enable the admin:
    (r'^accounts/', include(registration_urls)),
    (r'^accounts/', include(identity_association_urls)),
    (r'^static/(.*)', 'django.views.static.serve', 
        {'document_root': settings.MEDIA_ROOT}
    ),
)
