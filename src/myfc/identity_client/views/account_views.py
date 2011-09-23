# -*- coding: utf-8 -*-
import logging
import json
from datetime import datetime as dt

from django.conf import settings
from django import http

from identity_client.decorators import required_method
from identity_client.utils import get_account_module
from identity_client.models import Identity

@required_method('PUT')
def activate_account(request):

    status, message = 501, 'Not Implemented'
    return http.HttpResponse(message, status=status)
