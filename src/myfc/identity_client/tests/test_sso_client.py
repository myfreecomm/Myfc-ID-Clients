#coding: utf-8
import oauth2 as oauth
from mock import Mock
from httplib2 import Http, HttpLib2Error
import json

from django.test import TestCase
from django.conf import settings
from mock_helpers import *

from identity_client.sso.client import SSOClient


__all__ = ['SSOClientRequestToken', 'SSOClientAccessToken']


def create_signed_oauth_request(consumer, sso_client):

    plaintext_signature = oauth.SignatureMethod_PLAINTEXT()

    oauth_request = oauth.Request.from_consumer_and_token(consumer,
                                http_url=sso_client.request_token_url,
                                parameters={'scope':'sso-sample'})

    oauth_request.sign_request(plaintext_signature, consumer, None)

    #XXX: nao sabemos como passar o callback sem hack
    oauth_request['oauth_callback'] = 'http://callback.example.com'

    return oauth_request

def build_access_token_request(oauth_token, oauth_verifier):
    sso_client = SSOClient()

    secret = OAUTH_REQUEST_TOKEN_SECRET
    token = oauth.Token(key=oauth_token, secret=secret)
    token.set_verifier(oauth_verifier)

    consumer = oauth.Consumer(settings.MYFC_ID['CONSUMER_TOKEN'],
                               settings.MYFC_ID['CONSUMER_SECRET'])
    signature_method_plaintext = oauth.SignatureMethod_PLAINTEXT()
    oauth_request = oauth.Request.from_consumer_and_token(consumer, token=token,
                 http_url=sso_client.access_token_url, parameters={'scope':'sso-sample'})

    return oauth_request


class SSOClientRequestToken(TestCase):

    def setUp(self):
        self.sso_client = SSOClient()

    @patch_httplib2(Mock(return_value=mocked_request_token()))
    def test_fetch_request_token_succeeded(self):
        consumer = oauth.Consumer(settings.MYFC_ID['CONSUMER_TOKEN'],
                                   settings.MYFC_ID['CONSUMER_SECRET'])

        oauth_request = create_signed_oauth_request(consumer, self.sso_client)

        request_token = self.sso_client.fetch_request_token(oauth_request)

        self.assertEqual(OAUTH_REQUEST_TOKEN, request_token.key)
        self.assertEqual(OAUTH_REQUEST_TOKEN_SECRET, request_token.secret)

    @patch_httplib2(Mock(return_value=mocked_response(401, 'invalid token')))
    def test_fetch_request_token_fails_on_invalid_token(self):
        self.assertRaises(
            AssertionError, self.sso_client.fetch_request_token
        )

    @patch_httplib2(Mock(side_effect=AttributeError))
    def test_http_exceptions_are_not_handled(self):
        self.assertRaises(AttributeError, self.sso_client.fetch_request_token)


class SSOClientAccessToken(TestCase):

    def setUp(self):
        self.sso_client = SSOClient()

    @patch_httplib2(Mock(return_value=mocked_access_token()))
    def test_fetch_access_token_succeeded(self):
        access_token = self.sso_client.fetch_access_token()

        self.assertEqual(OAUTH_ACCESS_TOKEN, access_token.key)

    @patch_httplib2(Mock(return_value=mocked_response(401, 'invalid verifier')))
    def test_fetch_access_token_fails_on_invalid_verifier(self):
        self.assertRaises(
            AssertionError, self.sso_client.fetch_access_token
        )

    @patch_httplib2(Mock(return_value=mocked_response(401, 'invalid token')))
    def test_fetch_access_token_fails_on_invalid_token(self):
        self.assertRaises(
            AssertionError, self.sso_client.fetch_access_token
        )
