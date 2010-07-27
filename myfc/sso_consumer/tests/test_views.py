# -*- coding: utf-8 -*-

from httplib2 import Http
from mock import Mock, patch_object

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase

__all__ = ['SSOConsumerViewsTestCase']

# FIXME: duplicated from test_sso_client.py, refactor
OAUTH_REQUEST_TOKEN = 'dummyrequesttoken'
OAUTH_REQUEST_TOKEN_SECRET = 'dummyrequesttokensecret'

# FIXME: duplicated from test_sso_client.py, refactor
def mocked_response(status, content):
    response = Mock()
    response.status = status

    return response, content

# FIXME: duplicated from test_sso_client.py, refactor
def mocked_request_token():
    response = Mock()
    response.status = 200
    content = '&'.join(['oauth_token_secret=%s' % OAUTH_REQUEST_TOKEN_SECRET,
               'oauth_token=%s' % OAUTH_REQUEST_TOKEN,
               'oauth_callback_confirmed=true'])

    return response, content

class SSOConsumerViewsTestCase(TestCase):

    @patch_object(Http, 'request', Mock(return_value=mocked_request_token()))
    def test_request_token_success(self):
        response = self.client.get(reverse('sso_consumer:request_token'), {})

        authorization_url = '%(HOST)s/%(AUTHORIZATION_PATH)s' % settings.SSO

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'],
            authorization_url + '?oauth_token=' + OAUTH_REQUEST_TOKEN)

    @patch_object(Http, 'request', Mock(return_value=mocked_response(401, 'invalid token')))
    def test_request_token_fails_on_invalid_token(self):
        response = self.client.get(reverse('sso_consumer:request_token'), {})

        self.assertEqual(response.status_code, 500)

    # TODO: test_request_token_fails_on_broken_server => status code 502
