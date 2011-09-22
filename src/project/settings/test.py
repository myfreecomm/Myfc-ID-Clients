# -*- coding: utf-8 -*-
from common import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG

# Make this unique, and don't share it with anybody.
SECRET_KEY = '(gy8ie&gl+0^a62hw$q#+zj+uff1o$zmm!n#)t9c4*%0v8&c)&'

APPLICATION_HOST = 'http://172.16.1.1:8000'
LOGIN_REDIRECT_URL = '/client-app/profile/'

MYFC_ID['HOST'] = 'http://192.168.1.5:8001'
MYFC_ID['SLUG'] = 'myfc-id-clients'
MYFC_ID['CONSUMER_TOKEN'] = 'HJNjNXU1R3'
MYFC_ID['CONSUMER_SECRET'] = 'tskFmOZvvxW4eoqsMyx8ANqqnaPfZCbp'

import logging
logging.basicConfig(
    level = logging.WARN,
    format = "%(asctime)s - %(levelname)s - %(message)s",
    filename = '/dev/null',
    filemode = 'a',
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

NOSQL_DATABASES = {
    'NAME': 'identity_client',
    'HOST': 'localhost',
}

#PERSISTENCE_STRATEGY= 'mongoengine'
PERSISTENCE_STRATEGY= 'django_db'
