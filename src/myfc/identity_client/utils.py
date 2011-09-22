# -*- coding: utf-8 -*-
from django.forms.util import ErrorDict, ErrorList
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

def prepare_form_errors(error_dict):
    return ErrorDict((k, ErrorList(v)) for (k, v) in error_dict.items())


def get_account_module():
    try:
        module_name =  settings.SERVICE_ACCOUNT_MODULE
        app_name, model_name = module_name.split('.')

        models_name = '%s.models' % app_name
        models = __import__(models_name, fromlist=[models_name])

        return getattr(models, model_name)

    except AttributeError:
        return

    except (ValueError, ImportError):
        raise ImproperlyConfigured(
            'settings.SERVICE_ACCOUNT_MODULE: %s could not be imported' % module_name
        )
