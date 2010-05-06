#coding UTF-8
from django.test import TestCase
from django.core.urlresolvers import reverse

from identity_registration_client.forms import RegistrationForm


__all__ = ['TestApiRegistrationForm']

def create_post(**kwargs):
    post_data = {'first_name':'giuseppe',
                'password1':'1234567',
                'password2':'1234567',
                'last_name':'rocca',
                'email':'kiti@come.com',
                'tos':True}
    post_data.update(kwargs)
    return post_data

class TestApiRegistrationForm(TestCase):

    def test_validation_error_on_no_password_match(self):
        form = RegistrationForm(create_post(password1='123', password2='456'))
        self.assertFalse(form.is_valid())

    def test_validation_error_if_user_do_not_agree_with_tos(self):
        form = RegistrationForm(create_post(tos=False))
        self.assertFalse(form.is_valid())
