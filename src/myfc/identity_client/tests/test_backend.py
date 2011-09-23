# -*- coding: utf-8 -*-
from datetime import datetime as dt, timedelta
from mock import patch_object, Mock
from httplib2 import Http
import json

from django.conf import settings
from django.contrib.auth.models import AnonymousUser

from identity_client.models import Identity
from identity_client.backend import MyfcidAPIBackend, get_user
from identity_client.utils import get_account_module
from identity_client.tests.mock_helpers import *
from identity_client.tests.helpers import MyfcIDTestCase as TestCase

__all__ = ['TestMyfcidApiBackend', 'TestGetUser', 'TestFetchUserData']

def mock_response(status):
    mocked_response = Mock()
    mocked_response.status = status

    return mocked_response

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
    "is_active": true,
    "accounts": [
        {
            "plan_slug": "plus",
            "name": "Pessoal",
            "roles": ["owner"],
            "url": "http://192.168.1.48:8000/organizations/api/accounts/e823f8e7-962c-414f-b63f-6cf439686159/",
            "expiration": "%s",
            "external_id": null,
            "uuid": "e823f8e7-962c-414f-b63f-6cf439686159"
        },
        {
            "plan_slug": "max",
            "name": "Myfreecomm",
            "roles": ["owner"],
            "url": "http://192.168.1.48:8000/organizations/api/accounts/b39bad59-94af-4880-995a-04967b454c7a/",
            "expiration": "%s",
            "external_id": null,
            "uuid": "b39bad59-94af-4880-995a-04967b454c7a"
        }
    ]
}""" % (
    (dt.today() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'), 
    (dt.today() + timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S'), 
)

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

mocked_httplib2_request_success = Mock(
    return_value=(mock_response(200), mocked_user_json)
)
mocked_httplib2_request_failure = Mock(
    return_value=(mock_response(500), mocked_user_json)
)


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
        #Identity.objects.delete()
        mocked_user_data = json.loads(mocked_user_json)

        # Create a user
        user = Identity.objects.create(
            uuid=mocked_user_data['uuid'],
            email='user@domain.com',
            first_name='First',
            last_name='Last',
        )

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


    def test_auth_creates_user_accounts(self):
        # drible da vaca
        cache = getattr(settings, 'SERVICE_ACCOUNT_MODULE', None)
        settings.SERVICE_ACCOUNT_MODULE = 'identity_client.ServiceAccount'

        # Mockar leitura dos dados
        MyfcidAPIBackend.fetch_user_data = fetch_user_data_ok

        # Autenticar um usuário
        identity = MyfcidAPIBackend().authenticate('user@valid.com', 's3nH4')

        # Voltar a configuração original
        settings.SERVICE_ACCOUNT_MODULE = cache

        # O usuário deve ser membro de duas contas
        serviceAccountModel = get_account_module()
        accounts = serviceAccountModel.for_identity(identity)
        self.assertEquals(accounts.count(), 2)


    def test_auth_removes_user_from_old_accounts(self):
        # drible da vaca
        cache = getattr(settings, 'SERVICE_ACCOUNT_MODULE', None)
        settings.SERVICE_ACCOUNT_MODULE = 'identity_client.ServiceAccount'

        # Autenticar usuário com accounts
        MyfcidAPIBackend.fetch_user_data = fetch_user_data_ok
        identity = MyfcidAPIBackend().authenticate('user@valid.com', 's3nH4')

        # 2 contas devem ter sido criadas
        serviceAccountModel = get_account_module()
        accounts = serviceAccountModel.for_identity(identity)
        self.assertEquals(accounts.count(), 2)

        # Mockar leitura dos dados (sem accounts)
        mocked_data = json.loads(mocked_user_json)
        del(mocked_data['accounts'])
        mocked_user_json_without_accounts = json.dumps(mocked_data)
        MyfcidAPIBackend.fetch_user_data = lambda self, user, password: mocked_user_json_without_accounts

        # Autenticar o mesmo usuário, desta vez sem accounts
        identity = MyfcidAPIBackend().authenticate('user@valid.com', 's3nH4')

        # O usuário deve ter sido dissociado das accounts
        serviceAccountModel = get_account_module()
        accounts = serviceAccountModel.for_identity(identity)
        self.assertEquals(accounts.count(), 0)

        # Voltar a configuração original
        settings.SERVICE_ACCOUNT_MODULE = cache


    def test_auth_user_accounts_creation_fails_if_settings_are_wrong(self):
        # drible da vaca
        cache = getattr(settings, 'SERVICE_ACCOUNT_MODULE', None)
        settings.SERVICE_ACCOUNT_MODULE = 'unknown_app.UnknownModel'

        # Mockar leitura dos dados
        MyfcidAPIBackend.fetch_user_data = fetch_user_data_ok

        # Autenticar um usuário
        identity = MyfcidAPIBackend().authenticate('user@valid.com', 's3nH4')

        # A autenticação ocorreu com sucesso
        self.assertTrue(identity is not None)

        # Voltar a configuração original
        settings.SERVICE_ACCOUNT_MODULE = cache

        # Nenhuma conta deve ter sido criada
        serviceAccountModel = get_account_module()
        accounts = serviceAccountModel.for_identity(identity)
        self.assertEquals(accounts.count(), 0)


    def test_auth_user_accounts_creation_fails_if_settings_are_missing(self):
        # drible da vaca
        cache = getattr(settings, 'SERVICE_ACCOUNT_MODULE', None)
        settings.SERVICE_ACCOUNT_MODULE = None

        # Mockar leitura dos dados
        MyfcidAPIBackend.fetch_user_data = fetch_user_data_ok

        # Autenticar um usuário
        identity = MyfcidAPIBackend().authenticate('user@valid.com', 's3nH4')

        # A autenticação ocorreu com sucesso
        self.assertTrue(identity is not None)

        # Voltar a configuração original
        settings.SERVICE_ACCOUNT_MODULE = cache

        # Nenhuma conta deve ter sido criada
        serviceAccountModel = get_account_module()
        accounts = serviceAccountModel.for_identity(identity)
        self.assertEquals(accounts.count(), 0)



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


    def test_user_not_sent(self):
        user = get_user(userid=None)
        self.assertTrue(isinstance(user, AnonymousUser))


    def test_invalid_user(self):
        user = get_user(userid=42)
        self.assertTrue(isinstance(user, AnonymousUser))


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
