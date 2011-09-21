# -*- coding: utf-8 -*-
from mock import patch_object, Mock
from httplib2 import Http

import json
from django.contrib.auth.models import AnonymousUser

from identity_client.models import Identity
from identity_client.backend import MyfcidAPIBackend, get_user
from identity_client.tests.mock_helpers import *
from identity_client.test_helpers import MyfcIDTestClient as TestCase

__all__ = ['TestMyfcidApiBackend', 'TestGetUser', 'TestFetchUserData']

mocked_user_json = """{
    "last_name": "Doe",
    "services": ["financedesktop"],
    "timezone": null,
    "nickname": null,
    "first_name": "John",
    "language": null,
    "country": null,
    "cpf": null,
    "gender": null,
    "birth_date": "2010-05-04",
    "email": "jd@123.com",
    "uuid": "16fd2706-8baf-433b-82eb-8c7fada847da",
    "is_active": true
}"""

mocked_user_corrupted = """{
    "last_name": "Doe",
    "services": ["financedesktop"],
    "timezone": null,
    "nickname": null,
    "first_name": "John",
    "language": n
"""

fetch_user_data_ok = lambda self, user, password: mocked_user_json
fetch_user_data_corrupted = lambda self, user, password: mocked_user_corrupted
fetch_user_data_failed = lambda self, user, password: None


class TestMyfcidApiBackend(TestCase):

    def test_successful_auth(self):
        mocked_user_data = json.loads(mocked_user_json)

        # Mockar leitura dos dados
        MyfcidAPIBackend.fetch_user_data = fetch_user_data_ok

        # Autenticar um usuário
        identity = MyfcidAPIBackend().authenticate('user@valid.com', 's3nH4')

        # Checar se o usuário foi autenticado corretamente
        self.assertNotEqual(identity, None)
        self.assertEquals(identity.first_name, mocked_user_data['first_name'])
        self.assertEquals(identity.last_name, mocked_user_data['last_name'])
        self.assertEquals(identity.email, mocked_user_data['email'])
        self.assertEquals(identity.user_data, mocked_user_data)

        # Checar se o backend foi setado corretamente
        self.assertEquals(
            identity.backend,
            '%s.%s' % (MyfcidAPIBackend.__module__, 'MyfcidAPIBackend')
        )


    def test_failed_auth(self):
        # Mockar leitura dos dados
        MyfcidAPIBackend.fetch_user_data = fetch_user_data_failed

        # Autenticar um usuário
        identity = MyfcidAPIBackend().authenticate('user@invalid.com', 'senha')

        # Garantir que o usuario não foi autenticado
        self.assertEquals(identity, None)


    def test_auth_updates_user(self):
        mocked_user_data = json.loads(mocked_user_json)

        # Create a user
        user = Identity(
            uuid=mocked_user_data['uuid'],
            email='user@domain.com',
            first_name='First',
            last_name='Last',
        )
        user.save()

        # Mockar leitura dos dados
        MyfcidAPIBackend.fetch_user_data = fetch_user_data_ok

        # Autenticar um usuário
        identity = MyfcidAPIBackend().authenticate('user@valid.com', 's3nH4')

        # Checar se os dados do usuário foram atualizados
        self.assertEquals(identity.first_name, mocked_user_data['first_name'])
        self.assertEquals(identity.last_name, mocked_user_data['last_name'])
        self.assertEquals(identity.email, mocked_user_data['email'])
        self.assertEquals(identity.uuid, mocked_user_data['uuid'])


    def test_corrupted_api_response(self):
        # Mockar leitura dos dados
        MyfcidAPIBackend.fetch_user_data = fetch_user_data_corrupted

        # Autenticar um usuário
        identity = MyfcidAPIBackend().authenticate('user@valid.com', 's3nH4')

        # Garantir que o usuario não foi autenticado
        self.assertEquals(identity, None)


class TestGetUser(TestCase):

    def _create_user(self):
        # Mockar leitura dos dados
        MyfcidAPIBackend.fetch_user_data = fetch_user_data_ok

        # Autenticar um usuário
        return MyfcidAPIBackend().authenticate('user@existing.com', 's3nH4')


    def test_valid_user(self):
        identity = self._create_user()

        user = get_user(userid=identity.id)
        self.assertEquals(user, identity)


    def test_invalid_user(self):
        user = get_user(userid=42)
        self.assertTrue(isinstance(user, AnonymousUser))

################# Fetch User Data tests #####################
def mock_response(status):
    mocked_response = Mock()
    mocked_response.status = status

    return mocked_response

mocked_httplib2_request_success = Mock(
    return_value=(mock_response(200), mocked_user_json)
)
mocked_httplib2_request_failure = Mock(
    return_value=(mock_response(500), mocked_user_json)
)

class TestFetchUserData(TestCase):

    @patch_httplib2(mocked_httplib2_request_success)
    def test_fetch_user_data_with_success(self):
        api_backend = MyfcidAPIBackend()
        response_content = api_backend.fetch_user_data('user@email.com', 's3nH4')
        self.assertEquals(response_content, mocked_user_json)

    @patch_httplib2(mocked_httplib2_request_failure)
    def test_fetch_user_data_failure(self):
        api_backend = MyfcidAPIBackend()
        response_content = api_backend.fetch_user_data('user@email.com', 's3nH4')
        self.assertEquals(response_content, None)
