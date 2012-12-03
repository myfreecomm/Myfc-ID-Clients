# -*- coding: utf-8 -*-
from httplib2 import HttpLib2Error
from mock import Mock, patch
from oauth2 import Token
import json

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase

from mock_helpers import *
from identity_client.models import Identity
from identity_client.utils import get_account_module
from identity_client.sso.client import SSOClient
from identity_client.tests.test_backend import mocked_user_json, mocked_user_corrupted

__all__ = ['SSOFetchRequestTokenView', 'AccessUserData']

request_token_session = {OAUTH_REQUEST_TOKEN: OAUTH_REQUEST_TOKEN_SECRET}
dummy_access_token = Token(OAUTH_ACCESS_TOKEN, OAUTH_ACCESS_TOKEN_SECRET)
mocked_user_dict = json.loads(mocked_user_json)


class SSOFetchRequestTokenView(TestCase):

    @patch_httplib2(Mock(return_value=mocked_request_token()))
    def test_request_token_success(self):
        response = self.client.get(reverse('sso_consumer:request_token'), {})

        authorization_url = '%(HOST)s/%(AUTHORIZATION_PATH)s' % settings.MYFC_ID

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response['Location'],
            authorization_url + '?oauth_token=' + OAUTH_REQUEST_TOKEN
        )

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

    @patch_httplib2(Mock(return_value=mocked_response(200, 'invalid_request_token')))
    def test_handles_malformed_request_token(self):
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


class AccessUserData(TestCase):

    @patch_httplib2(Mock(return_value=mocked_request_token()))
    def setUp(self):
        response = self.client.get(reverse('sso_consumer:request_token'), {})
        self.assertEquals(response.status_code, 302)


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
        response = self.client.get(
            reverse('sso_consumer:callback'), {
                'oauth_token': OAUTH_REQUEST_TOKEN,
                'oauth_verifier': 'niceverifier'
            }, 
        )

        self.assertEqual(response.status_code, 502)


    @patch.object(SSOClient, 'fetch_access_token', Mock(return_value=dummy_access_token))
    @patch_httplib2(Mock(return_value=mocked_response(200, mocked_user_corrupted)))
    def test_access_user_data_fails_if_corrupted_data_is_received(self):
        response = self.client.get(
            reverse('sso_consumer:callback'), {
                'oauth_token': OAUTH_REQUEST_TOKEN,
                'oauth_verifier': 'niceverifier'
            }, 
        )

        self.assertEqual(response.status_code, 500)


    @patch.object(SSOClient, 'fetch_access_token', Mock(return_value=dummy_access_token))
    @patch_httplib2(Mock(return_value=mocked_response(200, mocked_user_json)))
    @patch('oauth2.Request.sign_request')
    def test_oauth_request_user_data_is_correctly_signed(self, sign_request_mock):
        response = self.client.get(
            reverse('sso_consumer:callback'), {
                'oauth_token': OAUTH_REQUEST_TOKEN,
                'oauth_verifier': 'niceverifier'
            }, 
        )

        self.assertTrue(isinstance(sign_request_mock.call_args[0][2], Token))


    @patch.object(SSOClient, 'fetch_access_token', Mock(return_value=dummy_access_token))
    @patch_httplib2(Mock(return_value=mocked_response(200, mocked_user_json)))
    def test_authentication_creates_local_user(self):
        Identity.objects.all().delete()

        response = self.client.get(
            reverse('sso_consumer:callback'), {
                'oauth_token': OAUTH_REQUEST_TOKEN,
                'oauth_verifier': 'niceverifier'
            }, 
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].endswith('/profile/'))

        self.assertEqual(Identity.objects.count(), 1)


    @patch.object(SSOClient, 'fetch_access_token', Mock(return_value=dummy_access_token))
    @patch_httplib2(Mock(return_value=mocked_response(200, mocked_user_json)))
    def test_authentication_creates_local_user_accounts(self):
        # drible da vaca
        cache = getattr(settings, 'SERVICE_ACCOUNT_MODULE', None)
        settings.SERVICE_ACCOUNT_MODULE = 'identity_client.ServiceAccount'

        serviceAccountModel = get_account_module()
        serviceAccountModel.objects.all().delete()

        response = self.client.get(
            reverse('sso_consumer:callback'), {
                'oauth_token': OAUTH_REQUEST_TOKEN,
                'oauth_verifier': 'niceverifier'
            }, 
      )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].endswith('/profile/'))

        self.assertEqual(serviceAccountModel.objects.count(), 2)

        # Voltar a configuração original
        settings.SERVICE_ACCOUNT_MODULE = cache
