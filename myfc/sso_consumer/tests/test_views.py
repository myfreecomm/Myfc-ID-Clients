# -*- coding: utf-8 -*-

from httplib2 import Http, HttpLib2Error
from mock import Mock, patch_object

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase

from mock_helpers import *

__all__ = ['SSOConsumerViewsTestCase']

class SSOConsumerViewsTestCase(TestCase):

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
    def test_request_token_fails_on_invalid_token(self):
        response = self.client.get(reverse('sso_consumer:request_token'), {})

        self.assertEqual(response.status_code, 500)
