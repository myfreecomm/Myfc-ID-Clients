# -*- coding: utf-8 -*-
from django.forms.util import ErrorDict, ErrorList

def prepare_form_errors(error_dict):
    return ErrorDict((k, ErrorList(v)) for (k, v) in error_dict.items())
