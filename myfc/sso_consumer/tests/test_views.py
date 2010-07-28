# -*- coding: utf-8 -*-

from httplib2 import Http, HttpLib2Error
from mock import Mock, patch_object, patch
from oauth2 import Token

from django.http import HttpResponse
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.contrib.sessions.backends.db import SessionStore

from mock_helpers import *
from sso_consumer.sso_client import SSOClient

__all__ = ['SSOFetchRequestTokenView', 'SSOFetchAccessToken',
           'AccessUserData']

def assertCalledWithParameterType(method, arg_number, arg_type):
    assert type(method.call_args[0][arg_number]) == arg_type

class SSOFetchRequestTokenView(TestCase):

    @patch_object(Http, 'request', Mock(return_value=mocked_request_token()))
    def test_request_token_success(self):
        response = self.client.get(reverse('sso_consumer:request_token'), {})

        authorization_url = '%(HOST)s/%(AUTHORIZATION_PATH)s' % settings.SSO

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'],
            authorization_url + '?oauth_token=' + OAUTH_REQUEST_TOKEN)


        session = self.client.session

        self.assertTrue('request_token' in session)
        self.assertTrue(OAUTH_REQUEST_TOKEN in session['request_token'])
        self.assertEqual(
                        session['request_token'][OAUTH_REQUEST_TOKEN],
                        OAUTH_REQUEST_TOKEN_SECRET
                        )


    @patch_object(Http, 'request', Mock(return_value=mocked_response(401, 'invalid token')))
    def test_request_token_fails_on_invalid_token(self):
        response = self.client.get(reverse('sso_consumer:request_token'), {})

        self.assertEqual(response.status_code, 500)

    @patch_object(Http, 'request', Mock(side_effect=HttpLib2Error))
    def test_request_token_fails_on_broken_oauth_provider(self):

        response = self.client.get(reverse('sso_consumer:request_token'), {})

        self.assertEqual(response.status_code, 502)

    @patch_object(Http, 'request', Mock(return_value=mocked_response(200, 'corrupted_data')))
    def test_request_token_fails_on_corrupted_data(self):
        response = self.client.get(reverse('sso_consumer:request_token'), {})

        self.assertEqual(response.status_code, 500)


request_token_session = {OAUTH_REQUEST_TOKEN: OAUTH_REQUEST_TOKEN_SECRET}

class SSOFetchAccessToken(TestCase):

    @patch_object(SessionStore, 'get', Mock(return_value=request_token_session))
    @patch_object(Http, 'request', Mock(return_value=mocked_access_token()))
    @patch('sso_consumer.views.access_protected_resources', Mock(return_value=HttpResponse('protected stuff')))
    def test_fetch_access_token_succeeded(self):

        response = self.client.get(reverse('sso_consumer:callback'),
                                   {'oauth_token': OAUTH_REQUEST_TOKEN,
                                    'oauth_verifier': 'niceverifier'}
                                  )

        from sso_consumer.views import access_protected_resources
        self.assertTrue(access_protected_resources.called)


    @patch('sso_consumer.views.access_protected_resources', Mock(return_value=HttpResponse('protected stuff')))
    @patch_object(SSOClient, 'fetch_access_token', Mock(return_value='access_token'))
    def test_fetch_access_token_fails_on_no_previous_request_token(self):

        response = self.client.get(reverse('sso_consumer:callback'),
                                   {'oauth_token': OAUTH_REQUEST_TOKEN,
                                    'oauth_verifier': 'niceverifier'}
                                  )

        from sso_consumer.views import access_protected_resources
        self.assertFalse(access_protected_resources.called)

        self.assertFalse(SSOClient.fetch_access_token.called)

        self.assertEqual(response.status_code, 400)

    @patch_object(SessionStore, 'get', Mock(return_value=request_token_session))
    @patch_object(Http, 'request', Mock(side_effect=HttpLib2Error))
    @patch('sso_consumer.views.access_protected_resources', Mock(return_value=HttpResponse('protected stuff')))
    def test_fetch_access_fails_if_provider_is_down(self):

        response = self.client.get(reverse('sso_consumer:callback'),
                                   {'oauth_token': OAUTH_REQUEST_TOKEN,
                                    'oauth_verifier': 'niceverifier'}
                                  )

        from sso_consumer.views import access_protected_resources
        self.assertFalse(access_protected_resources.called)

        self.assertEqual(response.status_code, 502)

    @patch_object(SessionStore, 'get', Mock(return_value=request_token_session))
    @patch_object(Http, 'request', Mock(return_value=mocked_response(200, 'corrupted data')))
    @patch('sso_consumer.views.access_protected_resources', Mock(return_value=HttpResponse('protected stuff')))
    def test_fetch_access_fails_on_corrupted_data_returned(self):

        response = self.client.get(reverse('sso_consumer:callback'),
                                   {'oauth_token': OAUTH_REQUEST_TOKEN,
                                    'oauth_verifier': 'niceverifier'}
                                  )

        from sso_consumer.views import access_protected_resources
        self.assertFalse(access_protected_resources.called)

        self.assertEqual(response.status_code, 500)

    @patch_object(SessionStore, 'get', Mock(return_value=request_token_session))
    @patch('oauth2.Request.sign_request')
    def test_oauth_request_is_correctly_signed(self, sign_request_mock):
        response = self.client.get(reverse('sso_consumer:callback'),
                                   {'oauth_token': OAUTH_REQUEST_TOKEN,
                                    'oauth_verifier': 'niceverifier'}
                                  )
        from oauth2 import Token

        assertCalledWithParameterType(sign_request_mock,
                                      arg_number=2,
                                      arg_type=Token)


dummy_access_token = Token(OAUTH_ACCESS_TOKEN, OAUTH_ACCESS_TOKEN_SECRET)

#TODO: remover duplicação
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

corrupted_user_data =  """{
    "last_name": null,
    "services": [],
    "timezone": null, """


class AccessUserData(TestCase):

    @patch_object(SessionStore, 'get', Mock(return_value=request_token_session))
    @patch_object(SSOClient, 'fetch_access_token', Mock(return_value=dummy_access_token))
    @patch_object(Http, 'request', Mock(return_value=mocked_response(200, mocked_user_json)))
    def test_access_user_data_successfuly(self):
        response = self.client.get(reverse('sso_consumer:callback'),
                                   {'oauth_token': OAUTH_REQUEST_TOKEN,
                                    'oauth_verifier': 'niceverifier'}
                                  )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user_data.html')

    @patch_object(SessionStore, 'get', Mock(return_value=request_token_session))
    @patch_object(SSOClient, 'fetch_access_token', Mock(return_value=dummy_access_token))
    @patch_object(Http, 'request', Mock(side_effect=HttpLib2Error))
    def test_access_user_data_fails_if_myfc_id_is_down(self):
        response = self.client.get(reverse('sso_consumer:callback'),
                                   {'oauth_token': OAUTH_REQUEST_TOKEN,
                                    'oauth_verifier': 'niceverifier'}
                                  )

        self.assertEqual(response.status_code, 502)

    @patch_object(SessionStore, 'get', Mock(return_value=request_token_session))
    @patch_object(SSOClient, 'fetch_access_token', Mock(return_value=dummy_access_token))
    @patch_object(Http, 'request', Mock(return_value=mocked_response(200, corrupted_user_data)))
    def test_access_user_data_fails_if_corrupted_data_is_received(self):
        response = self.client.get(reverse('sso_consumer:callback'),
                                   {'oauth_token': OAUTH_REQUEST_TOKEN,
                                    'oauth_verifier': 'niceverifier'}
                                  )

        self.assertEqual(response.status_code, 500)

    @patch_object(SessionStore, 'get', Mock(return_value=request_token_session))
    @patch_object(SSOClient, 'fetch_access_token', Mock(return_value=dummy_access_token))
    @patch_object(Http, 'request', Mock(return_value=mocked_response(200, mocked_user_json)))
    @patch('oauth2.Request.sign_request')
    def test_oauth_request_user_data_is_correctly_signed(self, sign_request_mock):
        response = self.client.get(reverse('sso_consumer:callback'),
                                   {'oauth_token': OAUTH_REQUEST_TOKEN,
                                    'oauth_verifier': 'niceverifier'}
                                  )
        from oauth2 import Token

        assertCalledWithParameterType(sign_request_mock,
                                      arg_number=2,
                                      arg_type=Token)
