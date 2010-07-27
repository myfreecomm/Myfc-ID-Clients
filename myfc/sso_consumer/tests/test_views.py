# -*- coding: utf-8 -*-

from httplib2 import Http, HttpLib2Error
from mock import Mock, patch_object, patch

from django.http import HttpResponse
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.contrib.sessions.backends.db import SessionStore

from mock_helpers import *
from sso_consumer.sso_client import SSOClient

__all__ = ['SSOFetchRequestTokenView', 'SSOFetchAccessToken']

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
