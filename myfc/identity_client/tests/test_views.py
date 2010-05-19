#coding: UTF-8
import json
from mock import patch_object, Mock, patch
from httplib2 import Http

from django.test import TestCase
from django.core.urlresolvers import reverse

from identity_client import views

def create_post(**kwargs):
    post_data = {
        'password':'1234567',
        'password2':'1234567',
        'email':'giuseppe@rocca.com',
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
    "session_token": "ce5a0d017d5fc09af55482daad763617",
    "country": null,
    "cpf": null,
    "gender": null,
    "birth_date": "2010-05-04",
    "email": "giuseppe@rocca.com",
    "uuid": "16fd2706-8baf-433b-82eb-8c7fada847da"
}"""

mocked_form_errors = """{
    "email":["usuario existente"]
}"""

corrupted_form_errors = """ { "email": [" """

class IdentityRegistrationTest(TestCase):

    @patch_object(Http, 'request', Mock(return_value=(mock_response(200),
                                                      mocked_user_json)))
    def test_successful_api_registration(self):
        response = self.client.post(reverse('registration_register'), create_post())
        self.assertEquals(302, response.status_code)

    @patch_object(Http, 'request', Mock(return_value=(mock_response(409),
                                                      mocked_form_errors)))
    def test_conflict_error_on_api_registration(self):
        response = self.client.post(reverse('registration_register'), create_post())
        form_errors = response.context['form'].errors
        self.assertEquals({u'email': [u'usuario existente']}, form_errors)

    @patch_object(Http, 'request', Mock(return_value=(mock_response(409),
                                                      corrupted_form_errors)))
    def test_corrupted_errors_returned_on_api_registration(self):
        response = self.client.post(reverse('registration_register'), create_post())
        form_errors = response.context['form'].errors
        self.assertEquals({'__all__':[u"Ops! Erro na transmissão dos dados. Tente de novo."]},
                           form_errors)

    @patch_object(views, 'invoke_registration_api', Mock())
    def test_form_renderization_because_of_empty_fields(self):
        empty_post_data = {
                    'password':'',
                    'password2':'',
                    'email':'',
                    }
        response = self.client.post(reverse('registration_register'), empty_post_data)
        self.assertFalse(views.invoke_registration_api.called)
