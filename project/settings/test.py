# -*- coding: utf-8 -*-
from settings import *

DEBUG = False

ADMINS = (
    ('Vitor M. A. da Cruz', 'vitor.mazzi@myfreecomm.com.br'),
)
MANAGERS = ADMINS

AUTH_BACKEND = 'dummy'

DATABASE_ENGINE = 'sqlite3'

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
