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

from identity_client.sso.client import SSOClient
from identity_client.backend import MyfcidAPIBackend
from identity_client.views.client_views import login_user


__all__ = ['fetch_request_token', 'fetch_access_token']


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


def _create_signed_oauth_request(url, **kwargs):

    consumer = oauth.Consumer(settings.MYFC_ID['CONSUMER_TOKEN'],
                              settings.MYFC_ID['CONSUMER_SECRET'])

    signature_method_plaintext = oauth.SignatureMethod_PLAINTEXT()

    signature_token = kwargs.pop('signature_token', None)

    oauth_request = oauth.Request.from_consumer_and_token(
                                            consumer,
                                            http_url=url,
                                            parameters={'scope': 'auth:api'},
                                            **kwargs
                                            )

    oauth_request.sign_request(signature_method_plaintext, consumer, signature_token)

    return oauth_request


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
def fetch_request_token(request):
    sso_client = SSOClient()

    oauth_request = _create_signed_oauth_request(sso_client.request_token_url)

    set_script_prefix(settings.APPLICATION_HOST)
    oauth_request['oauth_callback'] = reverse('sso_consumer:callback')

    request_token = sso_client.fetch_request_token(oauth_request)

    if hasattr(request_token, 'key') and hasattr(request_token, 'secret'):
        session_key = request.COOKIES.get(settings.SESSION_COOKIE_NAME, None)
        logging.info("Session %s data: %s" % (
            session_key, request.session.items()
        ))
    else:
        logging.error("could not fetch req token")
        return HttpResponseServerError()

    request.session['request_token'] = {
        request_token.key: request_token.secret
    }
    request.session.save()

    url = '%s/%s?oauth_token=%s' % (
        settings.MYFC_ID['HOST'], settings.MYFC_ID['AUTHORIZATION_PATH'], request_token.key
    )
    response = HttpResponseRedirect(url)

    return response


@handle_api_exception
def fetch_access_token(request):
    oauth_token = request.GET.get('oauth_token')
    oauth_verifier = request.GET.get('oauth_verifier')

    try:
        request_token = request.session['request_token']
    except KeyError:
        session_key = request.COOKIES.get(settings.SESSION_COOKIE_NAME, None)
        print "Request token not in session. Session %s data: %s" % (session_key, request.session.items())
        return HttpResponseBadRequest()

    secret = request_token[oauth_token]
    token = oauth.Token(key=oauth_token, secret=secret)
    token.set_verifier(oauth_verifier)

    client = SSOClient()

    oauth_request = _create_signed_oauth_request(client.access_token_url,
                                                 token=token,
                                                 signature_token=token,)

    access_token = client.fetch_access_token(oauth_request)

    if not access_token:
        print "could not fetch access token"
        return HttpResponseServerError()

    user_data = fetch_user_data(access_token)
    if user_data is None:
        print "could not fetch user data"
        return HttpResponseServerError()

    myfc_id_backend = MyfcidAPIBackend()
    identity = myfc_id_backend.create_local_identity(user_data)
    login_user(request, identity)

    return HttpResponseRedirect(reverse('user_profile'))


def fetch_user_data(access_token):

    client = SSOClient()
    oauth_request = _create_signed_oauth_request(
                            client.user_data_url,
                            token=access_token,
                            signature_token=access_token,
                        )

    user_data = client.access_user_data(oauth_request)

    try:
        user_data = json.loads(user_data)
    except ValueError:
        return None

    return user_data
