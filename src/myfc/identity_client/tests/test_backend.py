# -*- coding: utf-8 -*-
from datetime import datetime as dt, timedelta
from mock import Mock
from uuid import uuid4
import json

from django.conf import settings
from django.contrib.auth.models import AnonymousUser

from identity_client.models import Identity
from identity_client.backend import MyfcidAPIBackend, get_user
from identity_client.client_api_methods import APIClient
from identity_client.utils import get_account_module
from identity_client.tests.mock_helpers import *
from identity_client.tests.helpers import MyfcIDTestCase as TestCase

from mock import patch

__all__ = ['TestMyfcidApiBackend', 'TestGetUser', 'TestFetchUserData', 'TestFetchUserAccounts']

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

    @patch.object(MyfcidAPIBackend, 'fetch_user_data', fetch_user_data_ok)
    def test_successful_auth(self):
        mocked_user_data = json.loads(mocked_user_json)

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


    @patch.object(MyfcidAPIBackend, 'fetch_user_data', fetch_user_data_failed)
    def test_failed_auth(self):
        # Autenticar um usuário
        identity = MyfcidAPIBackend().authenticate('user@invalid.com', 'senha')

        # Garantir que o usuario não foi autenticado
        self.assertEquals(identity, None)


    @patch.object(MyfcidAPIBackend, 'fetch_user_data', fetch_user_data_ok)
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

        # Autenticar um usuário
        identity = MyfcidAPIBackend().authenticate('user@valid.com', 's3nH4')

        # Checar se os dados do usuário foram atualizados
        self.assertEquals(identity.first_name, mocked_user_data['first_name'])
        self.assertEquals(identity.last_name, mocked_user_data['last_name'])
        self.assertEquals(identity.email, mocked_user_data['email'])
        self.assertEquals(identity.uuid, mocked_user_data['uuid'])


    @patch.object(MyfcidAPIBackend, 'fetch_user_data', fetch_user_data_corrupted)
    def test_corrupted_api_response(self):
        # Autenticar um usuário
        identity = MyfcidAPIBackend().authenticate('user@valid.com', 's3nH4')

        # Garantir que o usuario não foi autenticado
        self.assertEquals(identity, None)


    @patch.object(MyfcidAPIBackend, 'fetch_user_data', fetch_user_data_ok)
    @patch.object(settings, 'SERVICE_ACCOUNT_MODULE', 'identity_client.ServiceAccount')
    def test_auth_creates_user_accounts(self):
        # Autenticar um usuário
        identity = MyfcidAPIBackend().authenticate('user@valid.com', 's3nH4')

        # O usuário deve ser membro de duas contas
        serviceAccountModel = get_account_module()
        accounts = serviceAccountModel.for_identity(identity)
        self.assertEquals(accounts.count(), 2)


    @patch.object(MyfcidAPIBackend, 'fetch_user_data', fetch_user_data_ok)
    @patch.object(settings, 'SERVICE_ACCOUNT_MODULE', 'identity_client.ServiceAccount')
    def test_auth_removes_user_from_old_accounts(self):
        # Autenticar usuário com accounts
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


    @patch.object(MyfcidAPIBackend, 'fetch_user_data', fetch_user_data_ok)
    def test_auth_user_accounts_creation_fails_if_settings_are_wrong(self):
        # drible da vaca
        cache = getattr(settings, 'SERVICE_ACCOUNT_MODULE', None)
        settings.SERVICE_ACCOUNT_MODULE = 'unknown_app.UnknownModel'

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


    @patch.object(MyfcidAPIBackend, 'fetch_user_data', fetch_user_data_ok)
    def test_auth_user_accounts_creation_fails_if_settings_are_missing(self):
        # drible da vaca
        cache = getattr(settings, 'SERVICE_ACCOUNT_MODULE', None)
        settings.SERVICE_ACCOUNT_MODULE = None

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

    @patch.object(MyfcidAPIBackend, 'fetch_user_data', fetch_user_data_ok)
    def _create_user(self):
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


class TestFetchUserAccounts(TestCase):

    accounts = [
            {
                "service_data": { "name": "Doutor Financas", "slug": "dr_financas" },
                "account_data": { "name": "Pessoal", "uuid": "e823f8e7-962c-414f-b63f-6cf439686159" },
                "plan_slug": "plus",
                "expiration": (dt.today() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
                "add_member_url": "http://localhost:8080/organizations/api/accounts/e823f8e7-962c-414f-b63f-6cf439686159/members/"
            },
            {
                "service_data": { "name": "Backup Online", "slug": "backup_online" },
                "account_data": { "name": "Account1", "uuid": "b39bad59-94af-4880-995a-04967b454c7a" },
                "plan_slug": "max",
                "expiration": (dt.today() + timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S'),
                "add_member_url": "http://localhost:8080/organizations/api/accounts/b39bad59-94af-4880-995a-04967b454c7a/members/"
            }
    ]

    mocked_httplib2_request_accounts_ok = Mock(
        return_value=(mock_response(200), json.dumps(accounts))
    )

    mocked_httplib2_request_accounts_error = Mock()

    mocked_httplib2_request_accounts_failure = Mock(
        return_value=(mock_response(400), 'BAD REQUEST')
    )

    mocked_httplib2_request_accounts_unexpected_error = Mock(
        return_value=(mock_response(200), None)
    )


    @patch_httplib2(mocked_httplib2_request_accounts_ok)
    def test_fetch_user_accounts_with_success(self):
        accounts, error = APIClient.fetch_user_accounts(uuid4())
        self.assertEquals(accounts, self.accounts)
        self.assertEquals(error, None)

    @patch_httplib2(mocked_httplib2_request_accounts_unexpected_error)
    def test_fetch_user_accounts_generates_error(self):
        accounts, error = APIClient.fetch_user_accounts(uuid4())
        self.assertEquals(accounts, [])
        self.assertEquals(error['status'], None)
        self.assertTrue('unexpected error' in error['message'])

    @patch_httplib2(mocked_httplib2_request_accounts_failure)
    def test_fetch_user_accounts_400(self):
        accounts, error = APIClient.fetch_user_accounts(uuid4())
        self.assertEquals(accounts, [])
        self.assertEquals(error['status'], 400)
        self.assertTrue('BAD REQUEST' in error['message'])

    @patch_httplib2(mocked_httplib2_request_accounts_error)
    def test_httplib2_error(self):
        def side_effect(*args, **kwargs):
            import httplib2
            raise httplib2.HttpLib2Error

        self.mocked_httplib2_request_accounts_error.side_effect = side_effect

        accounts, error = APIClient.fetch_user_accounts(uuid4())
        self.assertEquals(accounts, [])
        self.assertEquals(error['status'], None)
        self.assertTrue('connection error' in error['message'])
