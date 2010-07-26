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

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'],
            '%(HOST)s/%(AUTHORIZATION_PATH)s?oauth_token=' % settings.SSO
            + OAUTH_REQUEST_TOKEN)
