# -*- coding: utf-8 -*-
import json
from datetime import datetime as dt, timedelta
from httplib2 import HttpLib2Error

from mock import patch, Mock
import vcr

from django.conf import settings
from django.test import TestCase

from identity_client import client_api_methods
from identity_client.client_api_methods import APIClient
from identity_client.forms import RegistrationForm, IdentityInformationForm


mocked_accounts_json = '''[
    {
        "service_data": {
            "name": "John App", "slug": "johnapp"
        },
        "account_data": {
            "name": "Pessoal",
            "uuid": "e823f8e7-962c-414f-b63f-6cf439686159"
        },
        "plan_slug": "plus",
        "roles": ["owner"],
        "membership_details_url": "%s/organizations/api/accounts/e823f8e7-962c-414f-b63f-6cf439686159/members/1e73dad8-fefe-4b3a-a1a1-7149633748f2/",
        "url": "%s/organizations/api/accounts/e823f8e7-962c-414f-b63f-6cf439686159/",
        "expiration": "%s",
        "external_id": null
    },
    {
        "service_data": {
            "name": "John App", "slug": "johnapp"
        },
        "account_data": {
            "name": "Myfreecomm",
            "uuid": "b39bad59-94af-4880-995a-04967b454c7a"
        },
        "plan_slug": "seller",
        "roles": ["owner"],
        "membership_details_url": "%s/organizations/api/accounts/b39bad59-94af-4880-995a-04967b454c7a/members/1e73dad8-fefe-4b3a-a1a1-7149633748f2/",
        "url": "%s/organizations/api/accounts/b39bad59-94af-4880-995a-04967b454c7a/",
        "expiration": "%s",
        "external_id": null
    }
]''' % (
    settings.MYFC_ID['HOST'],
    settings.MYFC_ID['HOST'],
    (dt.today() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
    settings.MYFC_ID['HOST'],
    settings.MYFC_ID['HOST'],
    (dt.today() + timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
)


mocked_accounts_list = json.loads(mocked_accounts_json)

mocked_account_json = """{
        "service_data": {
            "name": "John App", "slug": "johnapp"
        },
        "account_data": {
            "name": "Pessoal",
            "uuid": "e823f8e7-962c-414f-b63f-6cf439686159"
        },
        "plan_slug": "plus",
        "roles": ["owner"],
        "membership_details_url": "%s/organizations/api/accounts/e823f8e7-962c-414f-b63f-6cf439686159/members/1e73dad8-fefe-4b3a-a1a1-7149633748f2/",
        "url": "%s/organizations/api/accounts/e823f8e7-962c-414f-b63f-6cf439686159/",
        "expiration": "%s",
        "external_id": null
    }""" % (
    settings.MYFC_ID['HOST'], settings.MYFC_ID['HOST'], (dt.today() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
    )

mocked_account = json.loads(mocked_account_json)


__all__ = [
    'InvokeRegistrationApi',
    'FetchIdentityData', 'FetchIdentityDataWithEmail',
    'UpdateUserApi',
    'FetchAssociationData', 'UpdateAssociationData',
    'TestFetchUserAccounts', 'TestCreateUserAccount',
]

test_user_email = 'identity_client@disposableinbox.com'
test_user_password = '*SudN7%r$MiYRa!E'
test_user_uuid = 'c3769912-baa9-4a0c-9856-395a706c7d57'


class InvokeRegistrationApi(TestCase):

    def setUp(self):
        self.registration_data = {
            'first_name': 'Myfc ID',
            'last_name': 'Clients',
            'email': test_user_email,
            'password': test_user_password,
            'password2': test_user_password,
            'tos': True,
        }

    @patch.object(APIClient, 'api_host', 'http://127.0.0.1:23')
    def test_request_with_wrong_api_host(self):
        form = RegistrationForm(self.registration_data)
        response = APIClient.invoke_registration_api(form)
        status_code, content, new_form = response

        self.assertEquals(status_code, 500)
        self.assertEquals(content, None)
        self.assertEquals(form.errors, {
            '__all__': [u'Ocorreu uma falha na comunicação com o Passaporte Web. Por favor tente novamente.']
        })

    def test_request_with_wrong_credentials(self):
        form = RegistrationForm(self.registration_data)
        APIClient.pweb.auth = ('?????', 'XXXXXX')

        with vcr.use_cassette('cassettes/api_client/invoke_registration_api/wrong_credentials'):
            response = APIClient.invoke_registration_api(form)
            status_code, content, new_form = response

        APIClient.pweb.auth = (settings.MYFC_ID['CONSUMER_TOKEN'], settings.MYFC_ID['CONSUMER_SECRET'])

        self.assertEquals(status_code, 401)
        self.assertEquals(content, None)
        self.assertEquals(form.errors, {
            '__all__': [u'Esta aplicação não está autorizada a utilizar o PassaporteWeb. Entre em contato com o suporte.']
        })

    def test_request_with_application_without_permissions(self):
        form = RegistrationForm(self.registration_data)

        with vcr.use_cassette('cassettes/api_client/invoke_registration_api/application_without_permissions'):
            response = APIClient.invoke_registration_api(form)
            status_code, content, new_form = response

        self.assertEquals(status_code, 403)
        self.assertEquals(content, None)
        self.assertEquals(form.errors, {
            '__all__': [u'Erro no servidor. Entre em contato com o suporte.']
        })

    def test_request_without_tos_set(self):
        form = RegistrationForm(self.registration_data)
        del(form.data['tos'])

        with vcr.use_cassette('cassettes/api_client/invoke_registration_api/without_tos_set'):
            response = APIClient.invoke_registration_api(form)
            status_code, content, new_form = response

        self.assertEquals(status_code, 400)
        self.assertEquals(content, None)
        self.assertEquals(form.errors, {
            u'tos': [u'Você precisa concordar com os Termos de Serviço']
        })

    def test_request_with_password_only_once(self):
        form = RegistrationForm(self.registration_data)
        del(form.data['password2'])

        with vcr.use_cassette('cassettes/api_client/invoke_registration_api/with_password_only_once'):
            response = APIClient.invoke_registration_api(form)
            status_code, content, new_form = response

        self.assertEquals(status_code, 400)
        self.assertEquals(content, None)
        self.assertEquals(form.errors, {
            u'password2': [u'Este campo é obrigatório.']
        })

    def test_request_with_passwords_not_matching(self):
        form = RegistrationForm(self.registration_data)
        form.data['password2'] = 'will not match'

        with vcr.use_cassette('cassettes/api_client/invoke_registration_api/with_passwords_not_matching'):
            response = APIClient.invoke_registration_api(form)
            status_code, content, new_form = response

        self.assertEquals(status_code, 400)
        self.assertEquals(content, None)
        self.assertEquals(form.errors, {
            u'__all__': [u"The two password fields didn't match."]
        })

    def test_registration_success(self):
        form = RegistrationForm(self.registration_data)

        with vcr.use_cassette('cassettes/api_client/invoke_registration_api/registration_success'):
            response = APIClient.invoke_registration_api(form)
            status_code, content, new_form = response

        self.assertEquals(status_code, 200)
        self.assertEquals(content, {
            u'first_name': u'Myfc ID',
            u'last_name': u'Clients',
            u'send_partner_news': False,
            u'uuid': u'c3769912-baa9-4a0c-9856-395a706c7d57',
            u'is_active': False,
            u'cpf': None,
            u'update_info_url': u'/accounts/api/identities/c3769912-baa9-4a0c-9856-395a706c7d57/',
            u'notifications': {u'count': 0, u'list': u'/notifications/api/'},
            u'accounts': [],
            u'send_myfreecomm_news': False,
            u'services': {u'identity_client': u'/accounts/api/service-info/c3769912-baa9-4a0c-9856-395a706c7d57/identity_client/'},
            u'email': u'identity_client@disposableinbox.com',
            u'profile_url': u'/accounts/api/identities/c3769912-baa9-4a0c-9856-395a706c7d57/profile/'
        })
        self.assertEquals(form.errors, {})

    def test_email_already_registered(self):
        form = RegistrationForm(self.registration_data)

        with vcr.use_cassette('cassettes/api_client/invoke_registration_api/email_already_registered'):
            response = APIClient.invoke_registration_api(form)
            status_code, content, new_form = response

        self.assertEquals(status_code, 409)
        self.assertEquals(content, None)
        self.assertEquals(form.errors, {
            u'email': [u'Este email já está cadastrado. Por favor insira outro email']
        })

    def test_cpf_already_registered(self):
        form = RegistrationForm(self.registration_data)
        form.data['email'] = 'identity_client+1@disposableinbox.com'
        form.data['cpf'] = '11111111111'

        with vcr.use_cassette('cassettes/api_client/invoke_registration_api/cpf_already_registered'):
            response = APIClient.invoke_registration_api(form)
            status_code, content, new_form = response

        self.assertEquals(status_code, 400)
        self.assertEquals(content, None)
        self.assertEquals(form.errors, {
            u'cpf': [u'Este número de CPF já está cadastrado.']
        })

    def test_invalid_cpf_pt1(self):
        form = RegistrationForm(self.registration_data)
        form.data['email'] = 'identity_client+1@disposableinbox.com'
        form.data['cpf'] = '1111111111122222222'

        with vcr.use_cassette('cassettes/api_client/invoke_registration_api/invalid_cpf_pt1'):
            response = APIClient.invoke_registration_api(form)
            status_code, content, new_form = response

        self.assertEquals(status_code, 400)
        self.assertEquals(content, None)
        self.assertEquals(form.errors, {
            u'cpf': [u'Certifique-se de que o valor tenha no máximo 14 caracteres (ele possui 19).']
        })

    def test_invalid_cpf_pt2(self):
        form = RegistrationForm(self.registration_data)
        form.data['email'] = 'identity_client+1@disposableinbox.com'
        form.data['cpf'] = 'asdfgqwertzxcvb'

        with vcr.use_cassette('cassettes/api_client/invoke_registration_api/invalid_cpf_pt2'):
            response = APIClient.invoke_registration_api(form)
            status_code, content, new_form = response

        self.assertEquals(status_code, 400)
        self.assertEquals(content, None)
        self.assertEquals(form.errors, {
            u'cpf': [u'Certifique-se de que o valor tenha no máximo 14 caracteres (ele possui 15).']
        })


class FetchIdentityData(TestCase):

    @patch.object(APIClient, 'api_host', 'http://127.0.0.1:23')
    def test_request_with_wrong_api_host(self):
        response = APIClient.fetch_identity_data(uuid=test_user_uuid)
        status_code, content = response

        self.assertEquals(status_code, None)
        self.assertEquals(content, {'status': None, 'message': 'Error connecting to PassaporteWeb'})

    def test_request_with_wrong_credentials(self):
        APIClient.pweb.auth = ('?????', 'XXXXXX')

        with vcr.use_cassette('cassettes/api_client/fetch_identity_data/wrong_credentials'):
            response = APIClient.fetch_identity_data(uuid=test_user_uuid)
            status_code, content = response

        APIClient.pweb.auth = (settings.MYFC_ID['CONSUMER_TOKEN'], settings.MYFC_ID['CONSUMER_SECRET'])

        self.assertEquals(status_code, 401)
        self.assertEquals(content, {'status': 401, 'message': '401 Client Error: UNAUTHORIZED'})

    def test_request_with_application_without_permissions(self):

        with vcr.use_cassette('cassettes/api_client/fetch_identity_data/application_without_permissions'):
            response = APIClient.fetch_identity_data(uuid=test_user_uuid)
            status_code, content = response

        self.assertEquals(status_code, 403)
        self.assertEquals(content, {'status': 403, 'message': '403 Client Error: FORBIDDEN'})

    def test_request_with_uuid_which_does_not_exist(self):

        with vcr.use_cassette('cassettes/api_client/fetch_identity_data/uuid_which_does_not_exist'):
            response = APIClient.fetch_identity_data(uuid='00000000-0000-0000-0000-000000000000')
            status_code, content = response

        self.assertEquals(status_code, 404)
        self.assertEquals(content['status'], 404)
        self.assertTrue(content['message'].startswith('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1/'))

    def test_success_request(self):

        with vcr.use_cassette('cassettes/api_client/fetch_identity_data/success'):
            response = APIClient.fetch_identity_data(uuid=test_user_uuid)
            status_code, content = response

        self.assertEquals(status_code, 200)
        self.assertEquals(content, {
            u'accounts': [],
            u'email': u'identity_client@disposableinbox.com',
            u'first_name': u'Myfc ID',
            u'is_active': False,
            u'last_name': u'Clients',
            u'notifications': {u'count': 0, u'list': u'/notifications/api/'},
            u'profile_url': u'/accounts/api/identities/c3769912-baa9-4a0c-9856-395a706c7d57/profile/',
            u'send_myfreecomm_news': False,
            u'send_partner_news': False,
            u'services': {u'identity_client': u'/accounts/api/service-info/c3769912-baa9-4a0c-9856-395a706c7d57/identity_client/'},
            u'update_info_url': u'/accounts/api/identities/c3769912-baa9-4a0c-9856-395a706c7d57/',
            u'uuid': u'c3769912-baa9-4a0c-9856-395a706c7d57'
        })


class FetchIdentityDataWithEmail(TestCase):

    @patch.object(APIClient, 'api_host', 'http://127.0.0.1:23')
    def test_request_with_wrong_api_host(self):
        response = APIClient.fetch_identity_data(email=test_user_email)
        status_code, content = response

        self.assertEquals(status_code, None)
        self.assertEquals(content, {'status': None, 'message': 'Error connecting to PassaporteWeb'})

    def test_request_with_wrong_credentials(self):
        APIClient.pweb.auth = ('?????', 'XXXXXX')

        with vcr.use_cassette('cassettes/api_client/fetch_identity_data_with_email/wrong_credentials'):
            response = APIClient.fetch_identity_data(email=test_user_email)
            status_code, content = response

        APIClient.pweb.auth = (settings.MYFC_ID['CONSUMER_TOKEN'], settings.MYFC_ID['CONSUMER_SECRET'])

        self.assertEquals(status_code, 401)
        self.assertEquals(content, {'status': 401, 'message': '401 Client Error: UNAUTHORIZED'})

    def test_request_with_application_without_permissions(self):

        with vcr.use_cassette('cassettes/api_client/fetch_identity_data_with_email/application_without_permissions'):
            response = APIClient.fetch_identity_data(email=test_user_email)
            status_code, content = response

        self.assertEquals(status_code, 403)
        self.assertEquals(content, {'status': 403, 'message': '403 Client Error: FORBIDDEN'})

    def test_request_with_email_which_does_not_exist(self):

        with vcr.use_cassette('cassettes/api_client/fetch_identity_data_with_email/email_which_does_not_exist'):
            response = APIClient.fetch_identity_data(email='nao_registrado@email.test')
            status_code, content = response

        self.assertEquals(status_code, 404)
        self.assertEquals(content['status'], 404)
        self.assertTrue(content['message'].startswith('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1/'))

    def test_success_request(self):

        with vcr.use_cassette('cassettes/api_client/fetch_identity_data_with_email/success'):
            response = APIClient.fetch_identity_data(email=test_user_email)
            status_code, content = response

        self.assertEquals(status_code, 200)
        self.assertEquals(content, {
            u'accounts': [],
            u'email': u'identity_client@disposableinbox.com',
            u'first_name': u'Myfc ID',
            u'is_active': False,
            u'last_name': u'Clients',
            u'notifications': {u'count': 0, u'list': u'/notifications/api/'},
            u'profile_url': u'/accounts/api/identities/c3769912-baa9-4a0c-9856-395a706c7d57/profile/',
            u'send_myfreecomm_news': False,
            u'send_partner_news': False,
            u'services': {u'identity_client': u'/accounts/api/service-info/c3769912-baa9-4a0c-9856-395a706c7d57/identity_client/'},
            u'update_info_url': u'/accounts/api/identities/c3769912-baa9-4a0c-9856-395a706c7d57/',
            u'uuid': u'c3769912-baa9-4a0c-9856-395a706c7d57'
        })


class UpdateUserApi(TestCase):
    """ Estes testes utilizam o usuário criado em InvokeRegistrationApi.  """

    def setUp(self):
        with vcr.use_cassette('cassettes/api_client/fetch_identity_data_with_email/success'):
            response = APIClient.fetch_identity_data(email=test_user_email)
            status_code, content = response

        assert status_code == 200
        self.user_data = content

        self.updated_user_data = {
            'first_name': 'Identity',
            'last_name': 'Client',
            'send_myfreecomm_news': True,
            'send_partner_news': True,
        }

    @patch.object(APIClient, 'api_host', 'http://127.0.0.1:23')
    def test_request_with_wrong_api_host(self):
        form = IdentityInformationForm(self.updated_user_data)
        response = APIClient.update_user_api(form, self.user_data['update_info_url'])
        status_code, content, new_form = response

        self.assertEquals(status_code, 500)
        self.assertEquals(content, None)
        self.assertEquals(form.errors, {
            '__all__': [u'Ocorreu uma falha na comunicação com o Passaporte Web. Por favor tente novamente.']
        })

    def test_request_with_wrong_credentials(self):
        form = IdentityInformationForm(self.updated_user_data)
        APIClient.pweb.auth = ('?????', 'XXXXXX')

        with vcr.use_cassette('cassettes/api_client/update_user_api/wrong_credentials'):
            response = APIClient.update_user_api(form, self.user_data['update_info_url'])
            status_code, content, new_form = response

        APIClient.pweb.auth = (settings.MYFC_ID['CONSUMER_TOKEN'], settings.MYFC_ID['CONSUMER_SECRET'])

        self.assertEquals(status_code, 401)
        self.assertEquals(content, None)
        self.assertEquals(form.errors, {
            '__all__': [u'Esta aplicação não está autorizada a utilizar o PassaporteWeb. Entre em contato com o suporte.']
        })

    def test_request_with_application_without_permissions(self):
        form = IdentityInformationForm(self.updated_user_data)

        with vcr.use_cassette('cassettes/api_client/update_user_api/application_without_permissions'):
            response = APIClient.update_user_api(form, self.user_data['update_info_url'])
            status_code, content, new_form = response

        self.assertEquals(status_code, 403)
        self.assertEquals(content, None)
        self.assertEquals(form.errors, {
            '__all__': [u'Erro no servidor. Entre em contato com o suporte.']
        })

    def test_cpf_already_registered(self):
        form = IdentityInformationForm(self.updated_user_data)
        form.data['cpf'] = '11111111111'

        with vcr.use_cassette('cassettes/api_client/update_user_api/cpf_already_registered'):
            response = APIClient.update_user_api(form, self.user_data['update_info_url'])
            status_code, content, new_form = response

        self.assertEquals(status_code, 409)
        self.assertEquals(content, None)
        self.assertEquals(form.errors, {
            u'cpf': [u'Esse número de CPF já está cadastrado.']
        })

    def test_invalid_cpf_pt1(self):
        form = IdentityInformationForm(self.updated_user_data)
        form.data['cpf'] = '1111111111122222222'

        with vcr.use_cassette('cassettes/api_client/update_user_api/invalid_cpf_pt1'):
            response = APIClient.update_user_api(form, self.user_data['update_info_url'])
            status_code, content, new_form = response

        self.assertEquals(status_code, 409)
        self.assertEquals(content, None)
        self.assertEquals(form.errors, {
            u'cpf': [u'Certifique-se de que o valor tenha no máximo 14 caracteres (ele possui 19).']
        })

    def test_invalid_cpf_pt2(self):
        form = IdentityInformationForm(self.updated_user_data)
        form.data['cpf'] = 'asdfgqwertzxcvb'

        with vcr.use_cassette('cassettes/api_client/update_user_api/invalid_cpf_pt2'):
            response = APIClient.update_user_api(form, self.user_data['update_info_url'])
            status_code, content, new_form = response

        self.assertEquals(status_code, 409)
        self.assertEquals(content, None)
        self.assertEquals(form.errors, {
            u'cpf': [u'Certifique-se de que o valor tenha no máximo 14 caracteres (ele possui 15).']
        })

    def test_success_request(self):
        form = IdentityInformationForm(self.updated_user_data)

        with vcr.use_cassette('cassettes/api_client/update_user_api/success'):
            response = APIClient.update_user_api(form, self.user_data['update_info_url'])
            status_code, content, new_form = response

        self.assertEquals(status_code, 200)
        self.assertEquals(content, {
            u'accounts': [],
            u'email': u'identity_client@disposableinbox.com',
            u'first_name': u'Identity',
            u'is_active': False,
            u'last_name': u'Client',
            u'notifications': {u'count': 0, u'list': u'/notifications/api/'},
            u'profile_url': u'/accounts/api/identities/c3769912-baa9-4a0c-9856-395a706c7d57/profile/',
            u'send_myfreecomm_news': True,
            u'send_partner_news': True,
            u'services': {u'identity_client': u'/accounts/api/service-info/c3769912-baa9-4a0c-9856-395a706c7d57/identity_client/'},
            u'update_info_url': u'/accounts/api/identities/c3769912-baa9-4a0c-9856-395a706c7d57/',
            u'uuid': u'c3769912-baa9-4a0c-9856-395a706c7d57',
        })
        self.assertEquals(form.errors, {})

    def test_success_request_with_cpf(self):
        form = IdentityInformationForm(self.updated_user_data)
        form.data['cpf'] = '99999999999'

        with vcr.use_cassette('cassettes/api_client/update_user_api/success_with_cpf'):
            response = APIClient.update_user_api(form, self.user_data['update_info_url'])
            status_code, content, new_form = response

        self.assertEquals(status_code, 200)
        self.assertEquals(content, {
            u'accounts': [],
            u'email': u'identity_client@disposableinbox.com',
            u'first_name': u'Identity',
            u'is_active': False,
            u'last_name': u'Client',
            u'notifications': {u'count': 0, u'list': u'/notifications/api/'},
            u'profile_url': u'/accounts/api/identities/c3769912-baa9-4a0c-9856-395a706c7d57/profile/',
            u'send_myfreecomm_news': True,
            u'send_partner_news': True,
            u'services': {u'identity_client': u'/accounts/api/service-info/c3769912-baa9-4a0c-9856-395a706c7d57/identity_client/'},
            u'update_info_url': u'/accounts/api/identities/c3769912-baa9-4a0c-9856-395a706c7d57/',
            u'uuid': u'c3769912-baa9-4a0c-9856-395a706c7d57',
            u'cpf': u'99999999999',
        })
        self.assertEquals(form.errors, {})


class FetchAssociationData(TestCase):

    def setUp(self):
        with vcr.use_cassette('cassettes/api_client/fetch_identity_data_with_email/success'):
            response = APIClient.fetch_identity_data(email=test_user_email)
            status_code, content = response

        assert status_code == 200
        self.user_data = content

    @patch.object(APIClient, 'api_host', 'http://127.0.0.1:23')
    def test_request_with_wrong_api_host(self):
        response = APIClient.fetch_association_data(self.user_data['services']['identity_client'])
        status_code, content = response

        self.assertEquals(status_code, 500)
        self.assertEquals(content, {'status': None, 'message': 'Error connecting to PassaporteWeb'})

    def test_request_with_wrong_credentials(self):
        APIClient.pweb.auth = ('?????', 'XXXXXX')

        with vcr.use_cassette('cassettes/api_client/fetch_association_data/wrong_credentials'):
            response = APIClient.fetch_association_data(self.user_data['services']['identity_client'])
            status_code, content = response

        APIClient.pweb.auth = (settings.MYFC_ID['CONSUMER_TOKEN'], settings.MYFC_ID['CONSUMER_SECRET'])

        self.assertEquals(status_code, 401)
        self.assertEquals(content, {
            'status': 401,
            'message': u'{"detail": "You need to login or otherwise authenticate the request."}'
        })

    def test_request_with_application_without_permissions(self):
        association_url =  self.user_data['services']['identity_client']
        association_url = association_url.replace('identity_client', 'ecommerce')

        with vcr.use_cassette('cassettes/api_client/fetch_association_data/application_without_permissions'):
            response = APIClient.fetch_association_data(association_url)
            status_code, content = response

        self.assertEquals(status_code, 403)
        self.assertEquals(content, {
            'status': 403,
            'message': u'{"detail": "You do not have permission to access this resource. You may need to login or otherwise authenticate the request."}'
        })

    def test_request_for_association_which_does_not_exist(self):
        association_url =  self.user_data['services']['identity_client']
        association_url = association_url.replace('identity_client', 'gFXrVmzDXXZm')

        with vcr.use_cassette('cassettes/api_client/fetch_association_data/association_which_does_not_exist'):
            response = APIClient.fetch_association_data(association_url)
            status_code, content = response

        self.assertEquals(status_code, 403)
        self.assertEquals(content, {
            'status': 403,
            'message': u'{"detail": "You do not have permission to access this resource. You may need to login or otherwise authenticate the request."}'
        })

    def test_success_without_data(self):
        with vcr.use_cassette('cassettes/api_client/fetch_association_data/success_without_data'):
            response = APIClient.fetch_association_data(self.user_data['services']['identity_client'])
            status_code, content = response

        self.assertEquals(status_code, 200)
        self.assertEquals(content, {u'is_active': True, u'slug': u'identity_client'})

    def test_success_with_data(self):
        with vcr.use_cassette('cassettes/api_client/fetch_association_data/success_with_data'):
            response = APIClient.fetch_association_data(self.user_data['services']['identity_client'])
            status_code, content = response

        self.assertEquals(status_code, 200)
        self.assertEquals(content, {
            u'timezone': u'America/Sao_Paulo',
            u'is_active': True,
            u'updated_at': u'2013-06-24 14:55:00',
            u'updated_by': u'identity_client.UpdateAssociationData',
            u'slug': u'identity_client'
        })


class UpdateAssociationData(TestCase):

    def setUp(self):
        with vcr.use_cassette('cassettes/api_client/fetch_identity_data_with_email/success'):
            response = APIClient.fetch_identity_data(email=test_user_email)
            status_code, content = response

        assert status_code == 200
        self.user_data = content

        self.association_data = {
            'updated_by': 'identity_client.UpdateAssociationData',
            'updated_at': '2013-06-24 14:55:00',
            'timezone': 'America/Sao_Paulo',
        }

    @patch.object(APIClient, 'api_host', 'http://127.0.0.1:23')
    def test_request_with_wrong_api_host(self):
        response = APIClient.update_association_data(self.association_data, self.user_data['services']['identity_client'])
        status_code, content = response

        self.assertEquals(status_code, 500)
        self.assertEquals(content, {'status': None, 'message': 'Error connecting to PassaporteWeb'})

    def test_request_with_wrong_credentials(self):
        APIClient.pweb.auth = ('?????', 'XXXXXX')

        with vcr.use_cassette('cassettes/api_client/update_association_data/wrong_credentials'):
            response = APIClient.update_association_data(self.association_data, self.user_data['services']['identity_client'])
            status_code, content = response

        APIClient.pweb.auth = (settings.MYFC_ID['CONSUMER_TOKEN'], settings.MYFC_ID['CONSUMER_SECRET'])

        self.assertEquals(status_code, 401)
        self.assertEquals(content, {
            'status': 401,
            'message': u'{"detail": "You need to login or otherwise authenticate the request."}'
        })

    def test_request_with_application_without_permissions(self):
        association_url =  self.user_data['services']['identity_client']
        association_url = association_url.replace('identity_client', 'ecommerce')

        with vcr.use_cassette('cassettes/api_client/update_association_data/application_without_permissions'):
            response = APIClient.update_association_data(self.association_data, association_url)
            status_code, content = response

        self.assertEquals(status_code, 403)
        self.assertEquals(content, {
            'status': 403,
            'message': u'{"detail": "You do not have permission to access this resource. You may need to login or otherwise authenticate the request."}'
        })

    def test_request_for_association_which_does_not_exist(self):
        association_url =  self.user_data['services']['identity_client']
        association_url = association_url.replace('identity_client', 'gFXrVmzDXXZm')

        with vcr.use_cassette('cassettes/api_client/update_association_data/association_which_does_not_exist'):
            response = APIClient.update_association_data(self.association_data, association_url)
            status_code, content = response

        self.assertEquals(status_code, 403)
        self.assertEquals(content, {
            'status': 403,
            'message': u'{"detail": "You do not have permission to access this resource. You may need to login or otherwise authenticate the request."}'
        })

    def test_success_with_data(self):
        with vcr.use_cassette('cassettes/api_client/update_association_data/success_with_data'):
            response = APIClient.update_association_data(self.association_data, self.user_data['services']['identity_client'])
            status_code, content = response

        self.assertEquals(status_code, 200)
        self.assertEquals(content, {
            u'timezone': u'America/Sao_Paulo',
            u'is_active': True,
            u'updated_at': u'2013-06-24 14:55:00',
            u'updated_by': u'identity_client.UpdateAssociationData',
            u'slug': u'identity_client'
        })

    def test_success_without_data(self):
        with vcr.use_cassette('cassettes/api_client/update_association_data/success_without_data'):
            response = APIClient.update_association_data({}, self.user_data['services']['identity_client'])
            status_code, content = response

        self.assertEquals(status_code, 200)
        self.assertEquals(content, {u'is_active': True, u'slug': u'identity_client'})

    def test_success_with_xml_payload(self):
        data_with_xml = self.association_data.copy()
        data_with_xml['payload'] = {
            'content-type': 'application/xml',
            'body': u'<?xml version="1.0" encoding="UTF-8" ?> <俄语>данные</俄语>'
        }

        with vcr.use_cassette('cassettes/api_client/update_association_data/success_with_xml_payload'):
            response = APIClient.update_association_data(data_with_xml, self.user_data['services']['identity_client'])
            status_code, content = response

        self.assertEquals(status_code, 200)
        self.assertEquals(content, {
            u'timezone': u'America/Sao_Paulo',
            u'is_active': True,
            u'updated_at': u'2013-06-24 14:55:00',
            u'updated_by': u'identity_client.UpdateAssociationData',
            u'slug': u'identity_client',
            u'payload': {
                u'content-type': u'application/xml',
                u'body': u'<?xml version="1.0" encoding="UTF-8" ?> <俄语>данные</俄语>'
            }
        })


class TestFetchUserAccounts(TestCase):

    @patch.object(APIClient, 'api_host', 'http://127.0.0.1:23')
    def test_request_with_wrong_api_host(self):
        response = APIClient.fetch_user_accounts(uuid=test_user_uuid)
        status_code, accounts, error = response

        self.assertEquals(status_code, 500)
        self.assertEquals(accounts, None)
        self.assertEquals(error, {'status': None, 'message': 'Error connecting to PassaporteWeb'})

    def test_request_with_wrong_credentials(self):
        APIClient.pweb.auth = ('?????', 'XXXXXX')

        with vcr.use_cassette('cassettes/api_client/fetch_user_accounts/wrong_credentials'):
            response = APIClient.fetch_user_accounts(uuid=test_user_uuid)
            status_code, accounts, error = response

        APIClient.pweb.auth = (settings.MYFC_ID['CONSUMER_TOKEN'], settings.MYFC_ID['CONSUMER_SECRET'])

        self.assertEquals(status_code, 401)
        self.assertEquals(accounts, None)
        self.assertEquals(error, {
            'status': 401,
            'message': u'{"detail": "You need to login or otherwise authenticate the request."}'
        })

    def test_request_with_application_without_permissions(self):
        with vcr.use_cassette('cassettes/api_client/fetch_user_accounts/application_without_permissions'):
            response = APIClient.fetch_user_accounts(uuid=test_user_uuid)
            status_code, accounts, error = response

        self.assertEquals(status_code, 403)
        self.assertEquals(accounts, None)
        self.assertEquals(error, {
            'status': 403,
            'message': u'{"detail": "You do not have permission to access this resource. You may need to login or otherwise authenticate the request."}'
        })

    def test_request_with_uuid_which_does_not_exist(self):
        with vcr.use_cassette('cassettes/api_client/fetch_user_accounts/uuid_which_does_not_exist'):
            response = APIClient.fetch_user_accounts(uuid='00000000-0000-0000-0000-000000000000')
            status_code, accounts, error = response

        self.assertEquals(status_code, 404)
        self.assertEquals(accounts, None)
        self.assertEquals(error, {
            'status': 404,
            'message': u'"Identity with uuid=00000000-0000-0000-0000-000000000000 does not exist"'
        })

    def test_success_without_accounts(self):
        with vcr.use_cassette('cassettes/api_client/fetch_user_accounts/success_without_accounts'):
            response = APIClient.fetch_user_accounts(test_user_uuid)
            status_code, accounts, error = response

        self.assertEquals(status_code, 200)
        self.assertEquals(accounts, [])
        self.assertEquals(error, None)

    def test_success_with_accounts(self):
        raise NotImplementedError
        with vcr.use_cassette('cassettes/api_client/fetch_user_accounts/success_with_accounts'):
            response = APIClient.fetch_user_accounts(test_user_uuid)
            status_code, accounts, error = response

        self.assertEquals(status_code, 200)
        self.assertEquals(accounts, None)
        self.assertEquals(error, None)

    def test_success_with_expired_accounts(self):
        raise NotImplementedError
        with vcr.use_cassette('cassettes/api_client/fetch_user_accounts/success_with_expired_accounts'):
            response = APIClient.fetch_user_accounts(test_user_uuid, include_expired_accounts=True)
            status_code, accounts, error = response

        self.assertEquals(status_code, 200)
        self.assertEquals(accounts, None)
        self.assertEquals(error, None)


class TestCreateUserAccount(TestCase):
    maxDiff = None
    mocked_content = mocked_account_json
    method = 'POST'
    uuid = 'some_uuid'
    url = '%s/%s' % (APIClient.api_host, 'organizations/api/identities/some_uuid/accounts/')
    body = json.dumps({'plan_slug': 'plan_slug', 'name': 'account_name', 'expiration': None})

    def setUp(self):
        self.headers = {
            'cache-control': 'no-cache',
            'content-length': str(len(self.body)),
            'content-type': 'application/json',
            'user-agent': 'myfc_id client',
            'accept': 'application/json',
            'authorization': 'Basic {0}'.format('{0}:{1}'.format(
                APIClient.api_user, APIClient.api_password).encode('base64').strip()
            ),
        }

    @patch('identity_client.client_api_methods.httplib2')
    def test_successful(self, mocked_http):
        mocked_http_object = mocked_http.Http()
        mocked_request = mocked_http_object.request
        mocked_response = Mock()
        mocked_request.return_value = mocked_response, self.mocked_content
        mocked_response.status = 200

        response = APIClient.create_user_account(self.uuid, 'account_name', 'plan_slug')
        mocked_request.assert_called_once_with(
            self.url, self.method, headers=self.headers, body=self.body
        )

        self.assertEquals(response, (mocked_account, None))


    @patch('identity_client.client_api_methods.httplib2')
    def test_error_in_json_loads(self, mocked_http):
        mocked_http_object = mocked_http.Http()
        mocked_request = mocked_http_object.request
        mocked_response = Mock()
        mocked_request.return_value = mocked_response, '<not a json>'
        mocked_response.status = 200

        response = APIClient.create_user_account(self.uuid, 'account_name', 'plan_slug')
        mocked_request.assert_called_once_with(
            self.url, self.method, headers=self.headers, body=self.body
        )

        self.assertEquals(response, (None, {'status': 200, 'message': '<not a json>'}))


    @patch('identity_client.client_api_methods.httplib2')
    def test_unexpected_status_code(self, mocked_http):
        mocked_http_object = mocked_http.Http()
        mocked_request = mocked_http_object.request
        mocked_response = Mock()
        mocked_request.return_value = mocked_response, '404 not found'
        mocked_response.status = 404

        response = APIClient.create_user_account(self.uuid, 'account_name', 'plan_slug')
        mocked_request.assert_called_once_with(
            self.url, self.method, headers=self.headers, body=self.body
        )

        self.assertEquals(response, (None, {'status': 404, 'message': '404 not found'}))


    @patch('identity_client.client_api_methods.httplib2')
    def test_httplib2error_error(self, mocked_http):
        mocked_http_object = mocked_http.Http()
        mocked_request = mocked_http_object.request
        mocked_response = Mock()
        mocked_request.side_effect = HttpLib2Error

        response = APIClient.create_user_account(self.uuid, 'account_name', 'plan_slug')
        mocked_request.assert_called_once_with(
            self.url, self.method, headers=self.headers, body=self.body
        )

        self.assertEquals(response, (
            None, {'message': u'unexpected error: (HttpLib2Error) ', 'status': None}
        ))


    @patch('identity_client.client_api_methods.httplib2')
    def test_any_other_exception(self, mocked_http):
        mocked_http_object = mocked_http.Http()
        mocked_request = mocked_http_object.request
        mocked_response = Mock()
        mocked_request.side_effect = Exception

        response = APIClient.create_user_account(self.uuid, 'account_name', 'plan_slug')
        mocked_request.assert_called_once_with(
            self.url, self.method, headers=self.headers, body=self.body
        )

        self.assertEquals(response, (
            None, {'message': u'unexpected error: (Exception) ', 'status': None}
        ))
