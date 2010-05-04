from django.conf import settings
from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^static/(.*)', 'django.views.static.serve', 
        {'document_root': settings.MEDIA_ROOT}
    ),
)
