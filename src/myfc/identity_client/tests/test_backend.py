# -*- coding: utf-8 -*-
from datetime import datetime as dt, timedelta
import json
from uuid import uuid4

from mock import Mock, patch
import vcr

from django.conf import settings
from django.contrib.auth.models import AnonymousUser

from identity_client.models import Identity
from identity_client.backend import MyfcidAPIBackend, get_user
from identity_client.utils import get_account_module
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

test_user_email = 'identity_client@disposableinbox.com'
test_user_password = '*SudN7%r$MiYRa!E'
test_user_uuid = 'c3769912-baa9-4a0c-9856-395a706c7d57'

class TestMyfcidApiBackend(TestCase):

    def test_successful_auth(self):
        # Autenticar um usuário
        with vcr.use_cassette('cassettes/api_client/myfcid_api_backend/success'):
            identity = MyfcidAPIBackend().authenticate(test_user_email, test_user_password)

        # Checar se o usuário foi autenticado corretamente
        self.assertNotEqual(identity, None)
        self.assertEquals(identity.first_name, 'Identity')
        self.assertEquals(identity.last_name, 'Client')
        self.assertEquals(identity.email, test_user_email)
        self.assertEquals(identity.user_data, {
            u'authentication_key': u'$2a$12$nA3ad2y5aSBlg80K9ekbNuvnRO1OI1WUKZyoJqWEhk.PQpD8.6jkS',
            u'email': u'identity_client@disposableinbox.com',
            u'first_name': u'Identity',
            u'id_token': u'729dd3a15cf03a80024d0986deee9ae91fdd5d834fabf6f9',
            u'is_active': True,
            u'last_name': u'Client',
            u'notifications': {u'count': 0, u'list': u'/notifications/api/'},
            u'profile_url': u'/accounts/api/identities/c3769912-baa9-4a0c-9856-395a706c7d57/profile/',
            u'send_myfreecomm_news': True,
            u'send_partner_news': True,
            u'update_info_url': u'/accounts/api/identities/c3769912-baa9-4a0c-9856-395a706c7d57/',
            u'uuid': u'c3769912-baa9-4a0c-9856-395a706c7d57'
        })

        # Checar se o backend foi setado corretamente
        self.assertEquals(
            identity.backend,
            '%s.%s' % (MyfcidAPIBackend.__module__, 'MyfcidAPIBackend')
        )


    def test_failed_auth(self):
        # Autenticar um usuário
        with vcr.use_cassette('cassettes/api_client/myfcid_api_backend/wrong_password'):
            identity = MyfcidAPIBackend().authenticate(test_user_email, 'senha errada')

        # Garantir que o usuario não foi autenticado
        self.assertEquals(identity, None)


    def test_auth_updates_user(self):
        # Create a user
        user = Identity.objects.create(uuid=test_user_uuid, email='vai_mudar@email.com')

        # Autenticar um usuário
        with vcr.use_cassette('cassettes/api_client/myfcid_api_backend/success'):
            identity = MyfcidAPIBackend().authenticate(test_user_email, test_user_password)

        # Checar se os dados do usuário foram atualizados
        self.assertEquals(identity.first_name, 'Identity')
        self.assertEquals(identity.last_name, 'Client') 
        self.assertEquals(identity.email, test_user_email)
        self.assertEquals(identity.uuid, test_user_uuid)


    #@patch.object(MyfcidAPIBackend, 'fetch_user_data', fetch_user_data_corrupted)
    #def test_corrupted_api_response(self):
    #    # Autenticar um usuário
    #    identity = MyfcidAPIBackend().authenticate('user@valid.com', 's3nH4')

    #    # Garantir que o usuario não foi autenticado
    #    self.assertEquals(identity, None)


    @patch.object(settings, 'SERVICE_ACCOUNT_MODULE', 'identity_client.ServiceAccount')
    def test_auth_creates_user_accounts(self):
        # Autenticar um usuário
        with vcr.use_cassette('cassettes/api_client/myfcid_api_backend/success'):
            identity = MyfcidAPIBackend().authenticate(test_user_email, test_user_password)

        # O usuário deve ser membro de uma conta
        serviceAccountModel = get_account_module()
        accounts = serviceAccountModel.for_identity(identity)
        self.assertEquals(accounts.count(), 1)


    @patch.object(settings, 'SERVICE_ACCOUNT_MODULE', 'identity_client.ServiceAccount')
    def test_auth_removes_user_from_old_accounts(self):
        # Autenticar usuário com accounts
        with vcr.use_cassette('cassettes/api_client/myfcid_api_backend/success'):
            identity = MyfcidAPIBackend().authenticate(test_user_email, test_user_password)

        # 1 conta deve ter sido criada
        serviceAccountModel = get_account_module()
        accounts = serviceAccountModel.for_identity(identity)
        self.assertEquals(accounts.count(), 1)

        raise NotImplementedError
        # Autenticar o mesmo usuário, desta vez sem accounts
        with vcr.use_cassette('cassettes/api_client/myfcid_api_backend/success_without_accounts'):
            identity = MyfcidAPIBackend().authenticate(test_user_email, test_user_password)

        # O usuário deve ter sido dissociado da account
        serviceAccountModel = get_account_module()
        accounts = serviceAccountModel.for_identity(identity)
        self.assertEquals(accounts.count(), 0)


    def test_auth_user_accounts_creation_fails_if_settings_are_wrong(self):
        with patch.object(settings, 'SERVICE_ACCOUNT_MODULE', 'unknown_app.UnknownModel'):
            with vcr.use_cassette('cassettes/api_client/myfcid_api_backend/success'):
                identity = MyfcidAPIBackend().authenticate(test_user_email, test_user_password)

        # A autenticação ocorreu com sucesso
        self.assertTrue(identity is not None)

        # Nenhuma conta deve ter sido criada
        serviceAccountModel = get_account_module()
        accounts = serviceAccountModel.for_identity(identity)
        self.assertEquals(accounts.count(), 0)


    def test_auth_user_accounts_creation_fails_if_settings_are_missing(self):
        with patch.object(settings, 'SERVICE_ACCOUNT_MODULE', None):
            with vcr.use_cassette('cassettes/api_client/myfcid_api_backend/success'):
                identity = MyfcidAPIBackend().authenticate(test_user_email, test_user_password)

        # A autenticação ocorreu com sucesso
        self.assertTrue(identity is not None)

        # Nenhuma conta deve ter sido criada
        serviceAccountModel = get_account_module()
        accounts = serviceAccountModel.for_identity(identity)
        self.assertEquals(accounts.count(), 0)


class TestGetUser(TestCase):

    def _create_user(self):
        # Autenticar um usuário
        with vcr.use_cassette('cassettes/api_client/myfcid_api_backend/success'):
            return MyfcidAPIBackend().authenticate(test_user_email, test_user_password)


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

    def test_fetch_user_data_with_success(self):
        with vcr.use_cassette('cassettes/api_client/myfcid_api_backend/success'):
            _, user_data, _ = MyfcidAPIBackend().fetch_user_data(test_user_email, test_user_password)

        self.assertEquals(user_data, {
            u'authentication_key': u'$2a$12$nA3ad2y5aSBlg80K9ekbNuvnRO1OI1WUKZyoJqWEhk.PQpD8.6jkS',
            u'email': u'identity_client@disposableinbox.com',
            u'first_name': u'Identity',
            u'id_token': u'729dd3a15cf03a80024d0986deee9ae91fdd5d834fabf6f9',
            u'is_active': True,
            u'last_name': u'Client',
            u'notifications': {u'count': 0, u'list': u'/notifications/api/'},
            u'profile_url': u'/accounts/api/identities/c3769912-baa9-4a0c-9856-395a706c7d57/profile/',
            u'send_myfreecomm_news': True,
            u'send_partner_news': True,
            u'update_info_url': u'/accounts/api/identities/c3769912-baa9-4a0c-9856-395a706c7d57/',
            u'uuid': u'c3769912-baa9-4a0c-9856-395a706c7d57'
        })

    def test_fetch_user_data_failure(self):
        with vcr.use_cassette('cassettes/api_client/myfcid_api_backend/wrong_password'):
            _, user_data, error = MyfcidAPIBackend().fetch_user_data(test_user_email, 'senha errada')

        self.assertEquals(user_data, None)
        self.assertEquals(error, {'status': 401, 'message': '401 Client Error: UNAUTHORIZED'})
