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
from django.core.urlresolvers import reverse

from identity_client.sso.client import SSOClient
from identity_client.backend import MyfcidAPIBackend
from identity_client.views.client_views import login_user


__all__ = ['initiate', 'fetch_user_data']


def handle_api_exception(view):
    def func(*args, **kwargs):
        try:
            return view(*args, **kwargs)
        except HttpLib2Error, e:
            logging.error(
                '%s: Error during http request: %s<%s>',
                view.__name__,  e, type(e)
            )
            return HttpResponseServerError(status=502)
        except (AssertionError, ), e:
            logging.error(
                '%s: Unexpected status code %s<%s>',
                view.__name__, e, type(e)
            )
            return HttpResponseServerError()
    func.__name__ = view.__name__
    func.__doc__  = view.__doc__
    return func


def render_sso_iframe(request):
    context = {
        'myfcid_host': settings.MYFC_ID['HOST'],
        'application_host': settings.APPLICATION_HOST,
        'application_slug': settings.MYFC_ID['SLUG'],
    }

    return render_to_response(
        'sso_iframe.html', 
        context, 
        context_instance=RequestContext(request)
    )


@handle_api_exception
def initiate(request):
    sso_client = SSOClient()

    sso_client.set_signature_method(oauth.SignatureMethod_PLAINTEXT())

    try:
        request_token = SSOClient().fetch_request_token()
        request.session['request_token'] = {
            request_token.key: request_token.secret
        }
        request.session.save()

        session_key = request.COOKIES.get(settings.SESSION_COOKIE_NAME, None)
        logging.debug("Session %s data: %s", session_key, request.session.items())

    except AssertionError, e:
        resp, content = e.args

        message = "Could not fetch request token. Response was {0} - {1}".format(
            resp.get('status'), content
        )
        logging.error(message)
        return HttpResponseServerError(content=message)

    except ValueError, e:
        message = "Invalid request token: {0}".format(request_token)
        logging.error(message)
        return HttpResponseServerError(content=message)

    authorization_url = '%s/%s?oauth_token=%s' % (
        settings.MYFC_ID['HOST'], settings.MYFC_ID['AUTHORIZATION_PATH'], request_token.key
    )
    response = HttpResponseRedirect(authorization_url)

    return response


@handle_api_exception
def fetch_user_data(request):

    try:
        request_token = request.session['request_token']

    except KeyError:
        session_key = request.COOKIES.get(settings.SESSION_COOKIE_NAME, None)
        message = "Request token not in session. Session {0} data: {1}".format(
            session_key, request.session.items()
        )
        logging.debug(message)
        return HttpResponseBadRequest(content=message)

    oauth_token = request.GET.get('oauth_token')
    oauth_verifier = request.GET.get('oauth_verifier')

    secret = request_token[oauth_token]

    request_token = oauth.Token(key=oauth_token, secret=secret)
    request_token.set_verifier(oauth_verifier)

    try:
        access_token = SSOClient(request_token).fetch_access_token()
        request.session['access_token'] = {
            access_token.key: access_token.secret
        }
        request.session.save()

    except AssertionError, e:
        resp, content = e.args

        message = "Could not fetch access token. Response was {0} - {1}".format(
            resp.get('status'), content
        )
        logging.error(message)
        return HttpResponseServerError(content=message)

    except ValueError, e:
        message = "Invalid access token: {0}".format(access_token)
        logging.error(message)
        return HttpResponseServerError(content=message)


    ##
    # -------------------- CUT HERE -------------------- 
    ##

    try:
        raw_user_data = SSOClient(access_token).post(SSOClient.user_data_url)
        identity = json.loads(
            raw_user_data, object_hook=as_local_identity
        )
        login_user(request, identity)

    except AssertionError, e:
        resp, content = e.args

        message = "Could not fetch user data. Response was {0} - {1}".format(
            resp.get('status'), content
        )
        logging.error(message)
        return HttpResponseServerError(content=message)

    except ValueError, e:
        message = "Invalid user data: {0}".format(raw_user_data)
        logging.error(message)
        return HttpResponseServerError(content=message)

    next_url = request.session.get('next_url', reverse('user_profile'))

    return HttpResponseRedirect(next_url)


def as_local_identity(data):

    if ('uuid' in data) and ('email' in data):
        return MyfcidAPIBackend().create_local_identity(data)

    return data
