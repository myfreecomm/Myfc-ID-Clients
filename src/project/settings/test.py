# -*- coding: utf-8 -*-
from common import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',     # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': '%s/simple.sqlite' % PROJECT_PATH,  # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

# Make this unique, and don't share it with anybody.
SECRET_KEY = '(gy8ie&gl+0^a62hw$q#+zj+uff1o$zmm!n#)t9c4*%0v8&c)&'

APPLICATION_HOST = 'http://172.16.1.1:8000'
LOGIN_REDIRECT_URL = '/client-app/profile/'

MYFC_ID['HOST'] = 'http://192.168.1.5:8001'
MYFC_ID['SLUG'] = 'myfc-id-clients'
MYFC_ID['CONSUMER_TOKEN'] = 'HJNjNXU1R3'
MYFC_ID['CONSUMER_SECRET'] = 'tskFmOZvvxW4eoqsMyx8ANqqnaPfZCbp'
