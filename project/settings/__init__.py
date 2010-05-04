# -*- encoding: utf-8 -*-
import os
import sys

PROJECT_PATH = os.path.realpath(
    os.path.join(os.path.dirname(__file__), os.path.pardir, os.path.pardir))

DEBUG = True
TEMPLATE_DEBUG = DEBUG


ADMINS = (
)

MANAGERS = ADMINS

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Sao_Paulo'
DATE_FORMAT = 'd/m/Y'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'pt-br'
DEFAULT_CHARSET='utf-8'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True
USE_L10N = True

# Should we add trailing slashes to the urls?
# This is only used if CommonMiddleware is installed (See the middleware docs)
APPEND_SLASH = False

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = '%s/media-root/' % PROJECT_PATH

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/static/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '%s/admin-media/' % MEDIA_URL

# A secret key for this particular Django installation. Used to provide a seed
# in secret-key hashing algorithms. Set this to a random string -- the longer,
# the better.
# Make this unique, and don't share it with anybody.
SECRET_KEY = 'yj(6p#8@fe34=mjm751)imn4avdgrwenlf-IFW-0JPb4-)gh=1f4eye'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'project.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    '%s/templates' % PROJECT_PATH,
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.sessions',
)

AUTHENTICATION_BACKENDS = ('django.contrib.auth.backends.ModelBackend',
                           'identity_auth.utils.MongoEngineBackend',)