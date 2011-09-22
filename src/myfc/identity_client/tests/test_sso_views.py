# -*- coding: utf-8 -*-
from httplib2 import Http, HttpLib2Error
from mock import Mock, patch
from oauth2 import Token
import json

from django.http import HttpResponse
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.contrib.sessions.backends.db import SessionStore

from mock_helpers import *
from identity_client.models import Identity
from identity_client.utils import get_account_module
from identity_client.sso.client import SSOClient
from identity_client.sso import views as sso_views
from identity_client.tests.test_backend import mocked_user_json, mocked_user_corrupted

__all__ = ['SSOFetchRequestTokenView', 'SSOFetchAccessToken', 'AccessUserData']

request_token_session = {OAUTH_REQUEST_TOKEN: OAUTH_REQUEST_TOKEN_SECRET}
dummy_access_token = Token(OAUTH_ACCESS_TOKEN, OAUTH_ACCESS_TOKEN_SECRET)
mocked_user_dict = json.loads(mocked_user_json)


def assertCalledWithParameterType(method, arg_number, arg_type):
    assert type(method.call_args[0][arg_number]) == arg_type


class SSOFetchRequestTokenView(TestCase):

    @patch_httplib2(Mock(return_value=mocked_request_token()))
    def test_request_token_success(self):
        response = self.client.get(reverse('sso_consumer:request_token'), {})

        authorization_url = '%(HOST)s/%(AUTHORIZATION_PATH)s' % settings.MYFC_ID

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


    @patch_httplib2(Mock(return_value=mocked_response(401, 'invalid token')))
    def test_request_token_fails_on_invalid_token(self):
        response = self.client.get(reverse('sso_consumer:request_token'), {})

        self.assertEqual(response.status_code, 500)

    @patch.object(SSOClient, 'fetch_request_token')
    def test_handles_malformed_request_token(self, fetch_request_token_mock):
        fetch_request_token_mock.return_value = 'invalid_request_token'
        response = self.client.get(reverse('sso_consumer:request_token'), {})

        self.assertEqual(response.status_code, 500)

    @patch_httplib2(Mock(side_effect=HttpLib2Error))
    def test_request_token_fails_on_broken_oauth_provider(self):

        response = self.client.get(reverse('sso_consumer:request_token'), {})

        self.assertEqual(response.status_code, 502)

    @patch_httplib2(Mock(return_value=mocked_response(200, 'corrupted_data')))
    def test_request_token_fails_on_corrupted_data(self):
        response = self.client.get(reverse('sso_consumer:request_token'), {})

        self.assertEqual(response.status_code, 500)
 

class SSOFetchAccessToken(TestCase):

    @patch_httplib2(Mock(return_value=mocked_request_token()))
    def setUp(self):
        self.client.get(reverse('sso_consumer:request_token'), {})


    @patch_httplib2(Mock(return_value=mocked_access_token()))
    @patch('identity_client.sso.views.fetch_user_data')
    def test_fetch_access_token_succeeded(self, fetch_user_data_mock):

        fetch_user_data_mock.return_value = json.loads(mocked_user_json)

        response = self.client.get(reverse('sso_consumer:callback'),
                                   {'oauth_token': OAUTH_REQUEST_TOKEN,
                                    'oauth_verifier': 'niceverifier'}
                                  )

        from identity_client.sso.views import fetch_user_data
        self.assertTrue(fetch_user_data.called)


    #@patch('django.contrib.sessions.backends.db.SessionStore.get', Mock(return_value=None))
    @patch('identity_client.sso.client.SSOClient.fetch_access_token', Mock())
    @patch.object(sso_views, 'fetch_user_data', Mock())
    def test_fetch_access_token_fails_on_no_previous_request_token(self):

        # Clean client session
        session = self.client.session
        del(session['request_token'])
        session.save()

        response = self.client.get(
            reverse('sso_consumer:callback'), {
                'oauth_token': OAUTH_REQUEST_TOKEN,
                'oauth_verifier': 'niceverifier'
            }
        )

        # We consider this a bad request
        self.assertEqual(response.status_code, 400)

        # No communications should have been made
        self.assertFalse(SSOClient.fetch_access_token.called)
        from identity_client.sso.views import fetch_user_data
        self.assertFalse(fetch_user_data.called)



    @patch_httplib2(Mock(side_effect=HttpLib2Error))
    @patch('identity_client.sso.views.fetch_user_data', Mock(return_value={'mocked_key': 'mocked value'}))
    def test_fetch_access_fails_if_provider_is_down(self):

        response = self.client.get(reverse('sso_consumer:callback'),
                                   {'oauth_token': OAUTH_REQUEST_TOKEN,
                                    'oauth_verifier': 'niceverifier'}
                                  )

        from identity_client.sso.views import fetch_user_data
        self.assertFalse(fetch_user_data.called)

        self.assertEqual(response.status_code, 502)

    @patch_httplib2(Mock(return_value=mocked_response(200, 'corrupted data')))
    @patch('identity_client.sso.views.fetch_user_data', Mock(return_value={'mocked_key': 'mocked value'}))
    def test_fetch_access_fails_on_corrupted_data_returned(self):

        response = self.client.get(reverse('sso_consumer:callback'),
                                   {'oauth_token': OAUTH_REQUEST_TOKEN,
                                    'oauth_verifier': 'niceverifier'}
                                  )

        from identity_client.sso.views import fetch_user_data
        self.assertFalse(fetch_user_data.called)

        self.assertEqual(response.status_code, 500)

    @patch_httplib2(Mock(return_value=mocked_access_token()))
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


class AccessUserData(TestCase):

    @patch_httplib2(Mock(return_value=mocked_request_token()))
    def setUp(self):
        self.client.get(reverse('sso_consumer:request_token'), {})


    @patch.object(SSOClient, 'fetch_access_token', Mock(return_value=dummy_access_token))
    @patch_httplib2(Mock(return_value=mocked_response(200, mocked_user_json)))
    def test_access_user_data_successfuly(self):

        response = self.client.get(
            reverse('sso_consumer:callback'), {
                'oauth_token': OAUTH_REQUEST_TOKEN,
                'oauth_verifier': 'niceverifier'
            }, 
      )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].endswith('/profile/'))
        self.assertNotEqual(self.client.session.get('user_data'), None)


    @patch.object(SSOClient, 'fetch_access_token', Mock(return_value=dummy_access_token))
    @patch_httplib2(Mock(side_effect=HttpLib2Error))
    def test_access_user_data_fails_if_myfc_id_is_down(self):
        response = self.client.get(reverse('sso_consumer:callback'),
                                   {'oauth_token': OAUTH_REQUEST_TOKEN,
                                    'oauth_verifier': 'niceverifier'}
                                  )

        self.assertEqual(response.status_code, 502)


    @patch.object(SSOClient, 'fetch_access_token', Mock(return_value=dummy_access_token))
    @patch_httplib2(Mock(return_value=mocked_response(200, mocked_user_corrupted)))
    def test_access_user_data_fails_if_corrupted_data_is_received(self):
        response = self.client.get(reverse('sso_consumer:callback'),
                                   {'oauth_token': OAUTH_REQUEST_TOKEN,
                                    'oauth_verifier': 'niceverifier'}
                                  )

        self.assertEqual(response.status_code, 500)


    @patch.object(SSOClient, 'fetch_access_token', Mock(return_value=dummy_access_token))
    @patch_httplib2(Mock(return_value=mocked_response(200, mocked_user_json)))
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


    @patch.object(SSOClient, 'fetch_access_token', Mock(return_value=dummy_access_token))
    @patch_httplib2(Mock(return_value=mocked_response(200, mocked_user_json)))
    def test_authentication_creates_local_user(self):
        local_users_count = Identity.objects.count()

        response = self.client.get(
            reverse('sso_consumer:callback'), {
                'oauth_token': OAUTH_REQUEST_TOKEN,
                'oauth_verifier': 'niceverifier'
            }, 
      )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].endswith('/profile/'))

        self.assertEqual(Identity.objects.count(), local_users_count+1)


    @patch.object(SSOClient, 'fetch_access_token', Mock(return_value=dummy_access_token))
    @patch_httplib2(Mock(return_value=mocked_response(200, mocked_user_json)))
    def test_authentication_creates_local_user_accounts(self):
        serviceAccountModel = get_account_module()
        local_accounts_count = serviceAccountModel.objects.count()

        response = self.client.get(
            reverse('sso_consumer:callback'), {
                'oauth_token': OAUTH_REQUEST_TOKEN,
                'oauth_verifier': 'niceverifier'
            }, 
      )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].endswith('/profile/'))

        self.assertEqual(serviceAccountModel.objects.count(), local_accounts_count+2)
