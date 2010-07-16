# -*- coding: utf-8 -*-

from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
import oauth2 as oauth
import httplib2


class SSOClient(oauth.Client):

    def __init__(self):
        self.request_token_url = '%(HOST)s/%(REQUEST_TOKEN_PATH)s' % settings.SSO
        self.access_token_url = '%(HOST)s/%(ACCESS_TOKEN_PATH)s' % settings.SSO

    def fetch_request_token(self, oauth_request):
        headers = oauth_request.to_header()
        #XXX: Por algum motivo o ouath2 tira o scope dos headers
        headers['Authorization'] = '%s, scope="%s"' %(headers['Authorization'], oauth_request['scope'])
        con = httplib2.Http()
        response, content = con.request(self.request_token_url, method="POST", headers=headers)
        return oauth.Token.from_string(content)

    def fetch_access_token(self, oauth_request):
        headers = oauth_request.to_header()
        #XXX: Por algum motivo o ouath2 tira o scope dos headers
        headers['Authorization'] = '%s, scope="%s"' %(headers['Authorization'], oauth_request['scope'])
        con = httplib2.Http()
        response, content = con.request(self.access_token_url, method="POST", headers=headers)
        return oauth.Token.from_string(content)

    def access_resource(self, oauth_request):
        """# via post body
        # -> some protected resources
        headers = {'Content-Type' :'application/x-www-form-urlencoded'}
        self.connection.request('POST', RESOURCE_URL, body=oauth_request.to_postdata(), headers=headers)
        response = self.connection.getresponse()
        return response.read()"""


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



    return HttpResponse(access_token.to_string())
