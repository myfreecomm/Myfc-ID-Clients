#coding: utf-8
import oauth2 as oauth
from mock import patch_object, Mock
from httplib2 import Http, HttpLib2Error
import json

from django.test import TestCase
from django.conf import settings

from sso_consumer.sso_client import SSOClient


__all__ = ['SSOClientRequestToken', 'SSOClientAccessToken',
            'SSOClientAccessUserData']


OAUTH_REQUEST_TOKEN = 'dummyrequesttoken'
OAUTH_REQUEST_TOKEN_SECRET = 'dummyrequesttokensecret'
OAUTH_ACCESS_TOKEN = 'dummyaccesstoken'
OAUTH_ACCESS_TOKEN_SECRET = 'dummyaccesstokensecret'

def mocked_response(status, content):
    response = Mock()
    response.status = status

    return response, content

def mocked_request_token():
    response = Mock()
    response.status = 200
    content = '&'.join(['oauth_token_secret=%s' % OAUTH_REQUEST_TOKEN_SECRET,
               'oauth_token=%s' % OAUTH_REQUEST_TOKEN,
               'oauth_callback_confirmed=true'])

    return response, content

def mocked_access_token():
    response = Mock()
    response.status = 200
    content = '&'.join(['oauth_token_secret=%s' % OAUTH_ACCESS_TOKEN_SECRET,
               'oauth_token=%s' % OAUTH_ACCESS_TOKEN])

    return response, content

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

    consumer = oauth.Consumer(settings.SSO['CONSUMER_TOKEN'],
                               settings.SSO['CONSUMER_SECRET'])
    signature_method_plaintext = oauth.SignatureMethod_PLAINTEXT()
    oauth_request = oauth.Request.from_consumer_and_token(consumer, token=token,
                 http_url=sso_client.access_token_url, parameters={'scope':'sso-sample'})

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

    @patch_object(Http, 'request', Mock(return_value=mocked_response(401, 'invalid token')))
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


class SSOClientAccessToken(TestCase):

    def setUp(self):
        self.sso_client = SSOClient()

    @patch_object(Http, 'request', Mock(return_value=mocked_access_token()))
    def test_fetch_access_token_succeeded(self):
        oauth_token = OAUTH_REQUEST_TOKEN
        oauth_verifier = 'dummyoauthverifier'

        oauth_request = build_access_token_request(oauth_token, oauth_verifier)

        access_token = self.sso_client.fetch_access_token(oauth_request)

        self.assertEqual(OAUTH_ACCESS_TOKEN, access_token.key)

    @patch_object(Http, 'request', Mock(return_value=mocked_response(401, 'invalid verifier')))
    def test_fetch_access_token_fails_on_invalid_verifier(self):
        oauth_token = OAUTH_REQUEST_TOKEN
        invalid_oauth_verifier = 'invalidoauthverifier'

        oauth_request = build_access_token_request(oauth_token, invalid_oauth_verifier)

        access_token = self.sso_client.fetch_access_token(oauth_request)

        self.assertEqual(access_token, None)

    @patch_object(Http, 'request', Mock(return_value=mocked_response(401, 'invalid token')))
    def test_fetch_access_token_fails_on_invalid_token(self):
        invalid_oauth_token = 'invalidtoken'
        oauth_verifier = 'dummyoauthverifier'

        oauth_request = build_access_token_request(invalid_oauth_token, oauth_verifier)

        access_token = self.sso_client.fetch_access_token(oauth_request)

        self.assertEqual(access_token, None)


mocked_user_json = """{
    "last_name": null,
    "services": [],
    "timezone": null,
    "nickname": null,
    "first_name": null,
    "language": null,
    "session_token": "ce5a0d017d5fc09af55482daad763617",
    "country": null,
    "cpf": null,
    "gender": null,
    "birth_date": "2010-05-04",
    "email": "giuseppe@rocca.com",
    "uuid": "16fd2706-8baf-433b-82eb-8c7fada847da"
}"""

class SSOClientAccessUserData(TestCase):

    @patch_object(Http, 'request', Mock(return_value=mocked_access_token()))
    def setUp(self):
        self.sso_client = SSOClient()
        oauth_token = OAUTH_REQUEST_TOKEN
        oauth_verifier = 'dummyoauthverifier'

        oauth_request = build_access_token_request(oauth_token, oauth_verifier)

        self.access_token = self.sso_client.fetch_access_token(oauth_request)

    @patch_object(Http, 'request', Mock(return_value=mocked_response(200, mocked_user_json)))
    def test_access_user_data(self):
        consumer = oauth.Consumer(settings.SSO['CONSUMER_TOKEN'], settings.SSO['CONSUMER_SECRET'])
        signature_method_plaintext = oauth.SignatureMethod_PLAINTEXT()

        oauth_request = oauth.Request.from_consumer_and_token(
                                                            consumer,
                                                            token=self.access_token,
                                                            http_url=self.sso_client.user_data_url,
                                                            parameters={'scope':'sso-sample'}
                                                            )
        oauth_request.sign_request(signature_method_plaintext, consumer, self.access_token)

        user_data = json.loads(self.sso_client.access_user_data(oauth_request))

        #TODO: Change the test to assert if the user is logged in
        self.assertTrue("uuid" in user_data)
        self.assertTrue("email" in user_data)

