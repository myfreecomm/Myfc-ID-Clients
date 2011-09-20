#coding: UTF-8
import json
from mock import Mock, patch
from httplib2 import Http

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.conf import settings

from identity_client.views import client_views
from identity_client.models import Identity
from identity_client.forms import IdentityAuthenticationForm

from identity_client import forms
from identity_client.tests.backend_mock import MyfcidAPIBackendMock
from identity_client.tests.mock_helpers import *


__all__ = ["IdentityRegistrationTest", "IdentityLoginTest"]


def create_post(**kwargs):
    post_data = {
        'password':'1234567',
        'password2':'1234567',
        'email':'giuseppe@rocca.com',
        'tos': True,
    }

    post_data.update(kwargs)
    return post_data

def mock_response(status_code):
    response = Mock()
    response.status = status_code
    return response

mocked_user_json = """{
    "last_name": null,
    "services": [],
    "timezone": null,
    "nickname": null,
    "first_name": null,
    "language": null,
    "country": null,
    "cpf": null,
    "gender": null,
    "birth_date": "2010-05-04",
    "email": "giuseppe@rocca.com",
    "uuid": "16fd2706-8baf-433b-82eb-8c7fada847da",
    "is_active": true
}"""

mocked_form_errors = """{
    "email":["usuario existente"]
}"""

corrupted_form_errors = """ { "email": [" """

class MockedBackendTestCase(TestCase):
    """
    Mock, Mock, Mock on heaven's dooooorr
    """
    def setUp(self):
        self.backend = forms.MyfcidAPIBackend
        forms.MyfcidAPIBackend = MyfcidAPIBackendMock

    def tearDown(self):
        forms.MyfcidAPIBackend = self.backend

class IdentityRegistrationTest(MockedBackendTestCase):


    @patch_httplib2(Mock(return_value=(mock_response(200), mocked_user_json)))
    def test_successful_api_registration(self):
        response = self.client.post(reverse('registration_register'), create_post())
        self.assertEquals(302, response.status_code)
        expected_user_data = json.loads(mocked_user_json)
        self.assertEquals(
            self.client.session['user_data']['uuid'],
            expected_user_data['uuid']
        )


    @patch_httplib2(Mock(return_value=(mock_response(409), mocked_form_errors)))
    def test_conflict_error_on_api_registration(self):
        response = self.client.post(reverse('registration_register'), create_post())
        form_errors = response.context['form'].errors
        self.assertEquals({u'email': [u'usuario existente']}, form_errors)


    @patch_httplib2(Mock(return_value=(mock_response(400), corrupted_form_errors)))
    def test_corrupted_errors_returned_on_api_registration(self):
        response = self.client.post(reverse('registration_register'), create_post())
        form_errors = response.context['form'].errors
        self.assertEquals({'__all__':[u"Ops! Erro na transmissão dos dados. Tente de novo."]},
                           form_errors)

    @patch.object(client_views, 'invoke_registration_api', Mock())
    def test_form_renderization_because_of_empty_fields(self):
        empty_post_data = {
                    'password':'',
                    'password2':'',
                    'email':'',
                    }
        response = self.client.post(reverse('registration_register'), empty_post_data)
        self.assertFalse(client_views.invoke_registration_api.called)


class IdentityLoginTest(MockedBackendTestCase):

    def test_successful_login(self):
        response = self.client.post(
            reverse('auth_login'),
            dict(email='jalim.habei@myfreecomm.com.br', password='1234567')
        )
        self.assertTrue('_auth_user_id' in self.client.session)


    def test_add_userdata_to_session_after_login(self):
        response = self.client.post(
            reverse('auth_login'),
            {'email': 'jalim.habei@myfreecomm.com.br', 'password':'1234567'}
        )
        self.assertEquals(
            self.client.session['user_data'], {}
        )
