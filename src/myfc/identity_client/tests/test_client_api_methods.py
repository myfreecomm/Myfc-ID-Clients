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
from identity_client.forms import RegistrationForm


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
    'TestCreateUserAccount',
    'TestFetchUserAccounts',
]

test_user_email = 'identity_client@disposableinbox.com'
test_user_password = '*SudN7%r$MiYRa!E'

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


class TestFetchUserAccounts(TestCase):
    mocked_content = mocked_accounts_json
    method = 'GET'
    headers = {
        'cache-control': 'no-cache',
        'content-length': '0',
        'content-type': 'application/json',
        'user-agent': 'myfc_id client',
        'authorization': 'Basic {0}'.format('{0}:{1}'.format(
            APIClient.api_user, APIClient.api_password).encode('base64').strip()
        ),
    }
    uuid = 'some_uuid'
    url = '%s/%s' % (APIClient.api_host, 'organizations/api/identities/some_uuid/accounts/')

    @patch('identity_client.client_api_methods.httplib2')
    def test_successful(self, mocked_http):
        mocked_http_object = mocked_http.Http()
        mocked_request = mocked_http_object.request
        mocked_response = Mock()
        mocked_request.return_value = mocked_response, self.mocked_content
        mocked_response.status = 200

        response = APIClient.fetch_user_accounts(self.uuid)
        mocked_request.assert_called_once_with(self.url, self.method, headers=self.headers)

        self.assertEquals(response, (mocked_accounts_list, None))

    def test_success(self):
        with vcr.use_cassette('cassettes/api_client/fetch_user_accounts/success'):
            user_uuid = '1cf30b5f-e78c-4eb9-a7b2-294a1d024e6d'
            response = APIClient.fetch_user_accounts(user_uuid)

        self.assertEquals(response, (mocked_accounts_list, None))

    def test_connection_error(self):

        with vcr.use_cassette('cassettes/api_client/fetch_user_accounts/connection_error'):
            response = APIClient.fetch_user_accounts(self.uuid)

        self.assertEquals(
            response, 
            (None, {'status': None, 'message': 'Error connecting to PassaporteWeb'})
        )

    @patch('identity_client.client_api_methods.httplib2')
    def test_error_in_json_loads(self, mocked_http):
        mocked_http_object = mocked_http.Http()
        mocked_request = mocked_http_object.request
        mocked_response = Mock()
        mocked_request.return_value = mocked_response, '<not a json>'
        mocked_response.status = 200

        response = APIClient.fetch_user_accounts(self.uuid)
        mocked_request.assert_called_once_with(self.url, self.method, headers=self.headers)

        self.assertEquals(response, ([], {'status': 200, 'message': '<not a json>'}))


    @patch('identity_client.client_api_methods.httplib2')
    def test_unexpected_status_code(self, mocked_http):
        mocked_http_object = mocked_http.Http()
        mocked_request = mocked_http_object.request
        mocked_response = Mock()
        mocked_request.return_value = mocked_response, '404 not found'
        mocked_response.status = 404

        response = APIClient.fetch_user_accounts(self.uuid)
        mocked_request.assert_called_once_with(self.url, self.method, headers=self.headers)

        self.assertEquals(response, ([], {'status': 404, 'message': '404 not found'}))


    @patch('identity_client.client_api_methods.httplib2')
    def test_httplib2error_error(self, mocked_http):
        mocked_http_object = mocked_http.Http()
        mocked_request = mocked_http_object.request
        mocked_response = Mock()
        mocked_request.side_effect = HttpLib2Error

        response = APIClient.fetch_user_accounts(self.uuid)
        mocked_request.assert_called_once_with(self.url, self.method, headers=self.headers)

        self.assertEquals(response, (
            [], {'message': u'unexpected error: (HttpLib2Error) ', 'status': None}
        ))


    @patch('identity_client.client_api_methods.httplib2')
    def test_any_other_exception(self, mocked_http):
        mocked_http_object = mocked_http.Http()
        mocked_request = mocked_http_object.request
        mocked_response = Mock()
        mocked_request.side_effect = Exception

        response = APIClient.fetch_user_accounts(self.uuid)
        mocked_request.assert_called_once_with(self.url, self.method, headers=self.headers)

        self.assertEquals(response, (
            [], {'message': u'unexpected error: (Exception) ', 'status': None}
        ))


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
