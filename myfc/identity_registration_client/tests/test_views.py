#coding UTF-8
from mock import patch_object, Mock
from httplib2 import Http

from django.test import TestCase
from django.core.urlresolvers import reverse

from identity_registration_client import views

def create_post(**kwargs):
    post_data = {'first_name':'giuseppe',
                'password1':'1234567',
                'password2':'1234567',
                'last_name':'rocca',
                'email':'giuseppe@rocca.com',
                'tos':True}
    post_data.update(kwargs)
    return post_data

def mock_response():
    response = Mock()
    response.status = 200
    return response

mocked_user_json = """{
    "last_name": "rocca",
    "services": [],
    "timezone": null,
    "nickname": null,
    "first_name": "giuseppe",
    "language": null,
    "session_token": "ce5a0d017d5fc09af55482daad763617",
    "country": null,
    "cpf": null,
    "gender": null,
    "birth_date": "2010-05-04",
    "email": "giuseppe@rocca.com"
}"""

class ApiRegistrationTest(TestCase):

    @patch_object(Http, 'request', Mock(return_value=(mock_response(),
                                                      mocked_user_json)))
    def test_successful_api_registration(self):

        response = self.client.post(reverse('register_account'), create_post())
        self.assertEquals(200, response.status_code)
