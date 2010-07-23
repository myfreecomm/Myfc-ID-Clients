#coding: utf-8
import oauth2 as oauth
from mock import patch_object, Mock
from httplib2 import Http, HttpLib2Error

from django.test import TestCase
from django.conf import settings

from sso_consumer.views import SSOClient


__all__ = ['SSOClientRequestToken']

OAUTH_REQUEST_TOKEN = 'dummyrequesttoken'
OAUTH_REQUEST_TOKEN_SECRET = 'dummyrequesttokensecret'

def mocked_request_token():
    response = Mock()
    response.status = 200
    content = '&'.join(['oauth_token_secret=%s' % OAUTH_REQUEST_TOKEN_SECRET,
               'oauth_token=%s' % OAUTH_REQUEST_TOKEN,
               'oauth_callback_confirmed=true'])

    return response, content

def create_signed_oauth_request(consumer, sso_client):

    plaintext_signature = oauth.SignatureMethod_PLAINTEXT()

    oauth_request = oauth.Request.from_consumer_and_token(consumer,
                                http_url=sso_client.request_token_url,
                                parameters={'scope':'sso-sample'})

    oauth_request.sign_request(plaintext_signature, consumer, None)

    #XXX: nao sabemos como passar o callback sem hack
    oauth_request['oauth_callback'] = 'http://example-callback.com'

    return oauth_request



class SSOClientRequestToken(TestCase):

    def setUp(self):
        self.sso_client = SSOClient()

    @patch_object(Http, 'request', Mock(return_value=mocked_request_token()))
    def test_fetch_request_token_succeeded(self):
        consumer = oauth.Consumer(settings.SSO['CONSUMER_TOKEN'],
                                   settings.SSO['CONSUMER_SECRET'])

        oauth_request = create_signed_oauth_request(consumer, self.sso_client)

        request_token = self.sso_client.fetch_request_token(oauth_request)

        self.assertEqual(OAUTH_REQUEST_TOKEN, request_token.key)
        self.assertEqual(OAUTH_REQUEST_TOKEN_SECRET, request_token.secret)

    @patch_object(Http, 'request', Mock(return_value=(401, 'invalid token')))
    def test_fetch_request_token_fails_on_invalid_token(self):
        consumer = oauth.Consumer('wrongtoken',
                                   settings.SSO['CONSUMER_SECRET'])

        oauth_request = create_signed_oauth_request(consumer, self.sso_client)

        request_token = self.sso_client.fetch_request_token(oauth_request)

        self.assertEqual(None, request_token)


    @patch_object(Http, 'request', Mock(side_effect=AttributeError))
    def test_fetch_request_token_fails_on_communication_error(self):
        consumer = oauth.Consumer(settings.SSO['CONSUMER_TOKEN'],
                                  settings.SSO['CONSUMER_SECRET'])

        oauth_request = create_signed_oauth_request(consumer, self.sso_client)

        self.assertRaises(HttpLib2Error, self.sso_client.fetch_request_token, oauth_request)


