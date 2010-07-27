# -*- coding: utf-8 -*-

import oauth2 as oauth
import json
from httplib2 import HttpLib2Error

from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.http import HttpResponseServerError
from django.http import HttpResponseBadRequest
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse

from sso_client import SSOClient


# TODO: remover duplicação de código

def _add_request_token_to_session(token, session):
    request_tokens = session.get('request_token', {})
    request_tokens[token.key] = token.secret
    session['request_token'] = request_tokens
    session.save()

def _create_signed_oauth_request(sso_client):

    consumer = oauth.Consumer(settings.SSO['CONSUMER_TOKEN'],
                              settings.SSO['CONSUMER_SECRET'])

    signature_method_plaintext = oauth.SignatureMethod_PLAINTEXT()

    oauth_request = oauth.Request.from_consumer_and_token(
                                            consumer,
                                            http_url=sso_client.request_token_url,
                                            parameters={'scope':'sso-sample'}
                                            )

    oauth_request.sign_request(signature_method_plaintext, consumer, None)

    return oauth_request


def fetch_request_token(request):
    sso_client = SSOClient()

    oauth_request = _create_signed_oauth_request(sso_client)

    #XXX: nao sabemos como passar o callback sem hack
    oauth_request['oauth_callback'] = request.build_absolute_uri(
                                                reverse('sso_consumer:callback')
                                                )

    try:
        request_token = sso_client.fetch_request_token(oauth_request)
    except HttpLib2Error:
        http_response_bad_gateway = HttpResponseServerError(status=502)

        return http_response_bad_gateway

    if not request_token:
        return HttpResponseServerError()

    _add_request_token_to_session(request_token, request.session)

    url = '%(HOST)s/%(AUTHORIZATION_PATH)s?oauth_token=%%s' % settings.SSO
    response = HttpResponseRedirect(url % request_token.key)

    return response


def fetch_access_token(request):
    oauth_token = request.GET.get('oauth_token')
    oauth_verifier = request.GET.get('oauth_verifier')
    request_token = request.session.get('request_token')

    if not request_token:
        return HttpResponseBadRequest()

    secret = request_token[oauth_token]
    token = oauth.Token(key=oauth_token, secret=secret)
    token.set_verifier(oauth_verifier)

    client = SSOClient()
    consumer = oauth.Consumer(settings.SSO['CONSUMER_TOKEN'], settings.SSO['CONSUMER_SECRET'])
    signature_method_plaintext = oauth.SignatureMethod_PLAINTEXT()
    oauth_request = oauth.Request.from_consumer_and_token(consumer, token=token,
                     http_url=client.access_token_url, parameters={'scope':'sso-sample'})
    oauth_request.sign_request(signature_method_plaintext, consumer, token)

    try:
        access_token = client.fetch_access_token(oauth_request)
    except HttpLib2Error:
        http_response_bad_gateway = HttpResponseServerError(status=502)

        return http_response_bad_gateway

    if not access_token:
        return HttpResponseServerError()

    return access_protected_resources(access_token)

def access_protected_resources(access_token):

    client = SSOClient()
    consumer = oauth.Consumer(settings.SSO['CONSUMER_TOKEN'], settings.SSO['CONSUMER_SECRET'])
    signature_method_plaintext = oauth.SignatureMethod_PLAINTEXT()
    oauth_request = oauth.Request.from_consumer_and_token(
                        consumer, token=access_token,
                        http_url=client.user_data_url,
                        parameters={'scope':'sso-sample'}
                    )
    oauth_request.sign_request(signature_method_plaintext, consumer, access_token)

    user_data = json.loads(client.access_user_data(oauth_request))

    return render_to_response('user_data.html', user_data)
