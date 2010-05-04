# -*- coding: utf-8 -*-
from settings import *

DEBUG = True

DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = '%s/myfc_id.sqlite' % PROJECT_PATH

EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = '%s/myfc_id.outbox' % PROJECT_PATH
