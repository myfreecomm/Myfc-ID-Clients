# -*- coding: utf-8 -*-
from settings import *

DEBUG = False

ADMINS = (
    ('Admin', 'admin@myfreecomm.com.br'),
)
MANAGERS = ADMINS

MIDDLEWARE_CLASSES = (
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',
)

CACHE_BACKEND = "locmem://?timeout=3601&max_entries=100"

DATABASE_ENGINE = 'postgresql_psycopg2'
DATABASE_NAME = '%(db_name)s'
DATABASE_USER = '%(db_user)s'
DATABASE_PASSWORD = '%(db_password)s'
DATABASE_HOST = 'localhost'
DATABASE_PORT = ''
