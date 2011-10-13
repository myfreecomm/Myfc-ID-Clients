# -*- coding: utf-8 -*-
import logging
import oauth2 as oauth
import json
from httplib2 import HttpLib2Error

from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.http import HttpResponseServerError, HttpResponseBadRequest
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse, set_script_prefix
from django.http import HttpResponse

from django.contrib.auth.decorators import login_required

from identity_client.backend import get_user_accounts


__all__ = ['list_accounts']

@login_required
def list_accounts(request):
    uuid = request.user.uuid
    accounts, error = get_user_accounts(uuid)
    context = {
        'error': error,
        'accounts': accounts,
    }

    return render_to_response('accounts_list.html',
        RequestContext(request, context))
