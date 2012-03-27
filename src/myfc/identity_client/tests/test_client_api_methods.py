# -*- coding: utf-8 -*-
import json
from datetime import datetime as dt, timedelta
from httplib2 import HttpLib2Error

from mock import patch, Mock

from django.test import TestCase

from identity_client.client_api_methods import APIClient


mocked_accounts_json = """[
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
        "membership_details_url": "http://192.168.1.48:8000/organizations/api/accounts/e823f8e7-962c-414f-b63f-6cf439686159/members/1e73dad8-fefe-4b3a-a1a1-7149633748f2/",
        "url": "http://192.168.1.48:8000/organizations/api/accounts/e823f8e7-962c-414f-b63f-6cf439686159/",
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
        "plan_slug": "max",
        "roles": ["owner"],
        "membership_details_url": "http://192.168.1.48:8000/organizations/api/accounts/b39bad59-94af-4880-995a-04967b454c7a/members/1e73dad8-fefe-4b3a-a1a1-7149633748f2/",
        "url": "http://192.168.1.48:8000/organizations/api/accounts/b39bad59-94af-4880-995a-04967b454c7a/",
        "expiration": "%s",
        "external_id": null
    }
]""" % (
    (dt.today() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
    (dt.today() + timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S'),
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
        "membership_details_url": "http://192.168.1.48:8000/organizations/api/accounts/e823f8e7-962c-414f-b63f-6cf439686159/members/1e73dad8-fefe-4b3a-a1a1-7149633748f2/",
        "url": "http://192.168.1.48:8000/organizations/api/accounts/e823f8e7-962c-414f-b63f-6cf439686159/",
        "expiration": "%s",
        "external_id": null
    }""" % (dt.today() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')

mocked_account = json.loads(mocked_account_json)


__all__ = ['TestFetchUserAccounts', 'TestCreateUserAccount']

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
