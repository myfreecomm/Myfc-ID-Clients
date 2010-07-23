# -*- coding: utf-8 -*-

from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
import oauth2 as oauth
import httplib2
import json


class SSOClient(oauth.Client):

    def __init__(self):
        self.request_token_url = '%(HOST)s/%(REQUEST_TOKEN_PATH)s' % settings.SSO
        self.access_token_url = '%(HOST)s/%(ACCESS_TOKEN_PATH)s' % settings.SSO
        self.user_data_url = '%(HOST)s/%(FETCH_USER_DATA_PATH)s' % settings.SSO


    def fetch_request_token(self, oauth_request):
        headers = oauth_request.to_header()
        #XXX: Por algum motivo o ouath2 tira o scope dos headers
        headers['Authorization'] = '%s, scope="%s"' %(headers['Authorization'], oauth_request['scope'])

        try:
            http = httplib2.Http()
            response, content = http.request(self.request_token_url,
                                             method="POST", headers=headers)
        except AttributeError:
            raise httplib2.HttpLib2Error

        try:
            token = oauth.Token.from_string(content)
        except ValueError:
            return None

        return token

    def fetch_access_token(self, oauth_request):
        headers = oauth_request.to_header()
        #XXX: Por algum motivo o ouath2 tira o scope dos headers
        headers['Authorization'] = '%s, scope="%s"' %(headers['Authorization'], oauth_request['scope'])
        con = httplib2.Http()
        response, content = con.request(self.access_token_url, method="POST", headers=headers)
        return oauth.Token.from_string(content)

    def access_user_data(self, oauth_request):
        headers = {'Content-Type' :'application/x-www-form-urlencoded'}
        con = httplib2.Http()
        response, content = con.request(self.user_data_url, method='POST',
                                    body=oauth_request.to_postdata(), headers=headers)
        return content


def request_token(request):
    client = SSOClient()
    consumer = oauth.Consumer(settings.SSO['CONSUMER_TOKEN'], settings.SSO['CONSUMER_SECRET'])
    signature_method_plaintext = oauth.SignatureMethod_PLAINTEXT()
    oauth_request = oauth.Request.from_consumer_and_token(consumer, http_url=client.request_token_url, parameters={'scope':'sso-sample'})
    oauth_request.sign_request(signature_method_plaintext, consumer, None)
    #XXX: nao sabemos como passar o callback sem hack
    oauth_request['oauth_callback'] = request.build_absolute_uri(reverse('sso_consumer:callback'))
    request_token = client.fetch_request_token(oauth_request)

    session = request.session.get('request_token', {})
    session[request_token.key] = request_token.secret
    request.session['request_token'] = session
    request.session.save()

    url = '%(HOST)s/%(AUTHORIZATION_PATH)s?oauth_token=%%s' % settings.SSO
    response = HttpResponseRedirect(url % request_token.key)

    return response


def request_access_token(request):
    oauth_token = request.GET.get('oauth_token')
    oauth_verifier = request.GET.get('oauth_verifier')

    secret = request.session['request_token'][oauth_token]
    token = oauth.Token(key=oauth_token, secret=secret)
    token.set_verifier(oauth_verifier)

    client = SSOClient()
    consumer = oauth.Consumer(settings.SSO['CONSUMER_TOKEN'], settings.SSO['CONSUMER_SECRET'])
    signature_method_plaintext = oauth.SignatureMethod_PLAINTEXT()
    oauth_request = oauth.Request.from_consumer_and_token(consumer, token=token,
                     http_url=client.access_token_url, parameters={'scope':'sso-sample'})
    oauth_request.sign_request(signature_method_plaintext, consumer, token)
    access_token = client.fetch_access_token(oauth_request)

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
