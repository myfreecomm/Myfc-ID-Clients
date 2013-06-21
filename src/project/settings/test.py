# -*- coding: utf-8 -*-
from common import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG

# Make this unique, and don't share it with anybody.
SECRET_KEY = '(gy8ie&gl+0^a62hw$q#+zj+uff1o$zmm!n#)t9c4*%0v8&c)&'

APPLICATION_HOST = 'http://172.16.1.1:8000'
LOGIN_REDIRECT_URL = '/developer/profile/'

MYFC_ID['HOST'] = 'https://sandbox.app.passaporteweb.com.br'
MYFC_ID['SLUG'] = 'identity_client'
MYFC_ID['CONSUMER_TOKEN'] = 'qxRSNcIdeA'
MYFC_ID['CONSUMER_SECRET'] = '1f0AVCZPJbRndF9FNSGMOWMfH9KMUDaX'

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

PERSISTENCE_STRATEGY= 'mongoengine_db'
