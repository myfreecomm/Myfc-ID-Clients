# -*- coding: utf-8 -*-
import json
from datetime import datetime as dt, timedelta
from uuid import uuid4
from collections import namedtuple

from django.conf import settings
from django.core.urlresolvers import reverse, NoReverseMatch

from identity_client.tests.helpers import MyfcIDTestCase as TestCase

from identity_client.utils import get_account_module


__all__ = ['TestActivateAccount', 'TestUpdateAccount']


RemoteAccount = namedtuple('RemoteAccount', [
    'uuid', 'name', 'service_name', 'service_slug', 'plan_slug', 'expiration', 'add_member_url'
])

account = RemoteAccount(
    uuid = '16fd2706-8baf-433b-82eb-8c7fada847da',
    name = 'Pessoal',
    service_name = 'Identity Client',
    service_slug = 'identity_client',
    plan_slug = 'plus',
    expiration = (dt.today() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
    add_member_url = 'http://192.168.1.48:8000/organizations/api/accounts/b39bad59-94af-4880-995a-04967b454c7a/members',
)

dict_mock = {
    u'account_data': {u'name': account.name, u'uuid': account.uuid},
    u'members_data': [],
    u'expiration': account.expiration,
    u'service_data': {u'name': account.service_name, u'slug': account.service_slug},
    u'plan_slug': account.plan_slug,
    u'add_member_url': account.add_member_url
}


def build_auth_header(login, password):
    return 'Basic %s' % (
        '%s:%s' % (
            login,
            password
        )
    ).encode('base64')


class TestActivateAccount(TestCase):

    url_name = 'account_activation'
    method = 'PUT'
    default_headers = {}
    auth = build_auth_header(
        settings.ACTIVATION_API['TOKEN'],
        settings.ACTIVATION_API['SECRET'],
    )

    def setUp(self):
        self.url = reverse(self.url_name, args=[str(uuid4())])

    def make_request(self, url, *args, **kwargs):
        client_method = getattr(self.client, self.http_method.lower())
        return client_method(url, *args, **kwargs)

    def test_GET_is_not_allowed(self):
        response = self.client.get(self.url, HTTP_AUTHORIZATION=self.auth)
        
        self.assertEqual(response.status_code, 405)

        data = json.loads(response.content)
        self.assertEqual(data, {u'detail': u"Method 'GET' not allowed on this resource."})

    def test_POST_is_not_allowed(self):
        response = self.client.post(self.url, HTTP_AUTHORIZATION=self.auth)
        
        self.assertEqual(response.status_code, 405)

        data = json.loads(response.content)
        self.assertEqual(data, {u'detail': u"Method 'POST' not allowed on this resource."})

    def test_DELETE_is_not_allowed(self):
        response = self.client.delete(self.url, HTTP_AUTHORIZATION=self.auth)
        
        self.assertEqual(response.status_code, 405)

        data = json.loads(response.content)
        self.assertEqual(data, {u'detail': u"Method 'DELETE' not allowed on this resource."})

    def test_PUT_is_allowed(self):
        response = self.client.put(self.url, HTTP_AUTHORIZATION=self.auth)

        # No data was sent, so this is a bad request
        self.assertEqual(response.status_code, 400)

        data = json.loads(response.content)
        self.assertEqual(data, {
            u'errors': [u'Not enought data for activation.'],
            u'field-errors': {u'expiration': [u'This field is required.']}
        })

    def test_requests_must_be_authenticated(self):
        response = self.client.put(self.url)

        # Without credentials we must receive a 403
        self.assertEqual(response.status_code, 403)

    def test_invalid_uuid_has_no_url_mapping(self):
        self.assertRaises(
            NoReverseMatch, reverse, self.url_name, args=[u'não é um uuid']
        )

    def test_missing_keys_are_reported_one_by_one_stage1(self):
        local_dict = dict_mock.copy()
        del(local_dict['plan_slug'])
        local_mock = json.dumps(local_dict)

        response = self.client.put(self.url, 
            local_mock, 
            content_type = 'application/json',
            HTTP_ACCEPT = 'application/json',
            HTTP_AUTHORIZATION=self.auth
        )

        self.assertEqual(response.status_code, 400)

        data = json.loads(response.content)
        self.assertEqual(data, {
            u'errors': [u'Not enought data for activation.'],
            u'field-errors': {u'plan_slug': [u'This field is required.']}
        })

    def test_missing_keys_are_reported_one_by_one_stage2(self):
        local_dict = dict_mock.copy()
        del(local_dict['account_data'])
        del(local_dict['plan_slug'])
        local_mock = json.dumps(local_dict)

        response = self.client.put(self.url, 
            local_mock, 
            content_type = 'application/json',
            HTTP_ACCEPT = 'application/json',
            HTTP_AUTHORIZATION=self.auth
        )

        self.assertEqual(response.status_code, 400)

        data = json.loads(response.content)
        self.assertEqual(data, {
            u'errors': [u'Not enought data for activation.'],
            u'field-errors': {u'account_data': [u'This field is required.']}
        })

    def test_api_does_not_accept_xml(self):
        response = self.client.put(self.url, 
            '<?xml version="1.0" encoding="utf-8"?><root></root>', 
            content_type = 'application/xml',
            HTTP_ACCEPT = 'application/xml',
            HTTP_AUTHORIZATION=self.auth
        )

        self.assertEqual(response.status_code, 415)

    def test_api_accepts_json(self):
        response = self.client.put(self.url, 
            json.dumps(dict_mock), 
            content_type = 'application/json',
            HTTP_ACCEPT = 'application/json',
            HTTP_AUTHORIZATION=self.auth
        )

        self.assertEqual(response.status_code, 200)

    def test_creates_account_on_success(self):
        serviceAccount =  get_account_module()
        self.assertEqual(serviceAccount.objects.count(), 0)

        response = self.client.put(self.url, 
            json.dumps(dict_mock), 
            content_type = 'application/json',
            HTTP_ACCEPT = 'application/json',
            HTTP_AUTHORIZATION=self.auth
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(serviceAccount.objects.count(), 1)
        new_account = serviceAccount.objects.get(uuid=account.uuid)
        
        for field in ('uuid', 'name', 'plan_slug'):
            self.assertEqual(
                getattr(account, field), getattr(new_account, field)
            )

        self.assertEqual(
            account.expiration, new_account.expiration.strftime('%Y-%m-%d %H:%M:%S')
        )

    def test_creates_account_without_expiration(self):
        serviceAccount =  get_account_module()
        self.assertEqual(serviceAccount.objects.count(), 0)

        local_mock = dict_mock.copy()
        local_mock['expiration'] = None

        response = self.client.put(self.url, 
            json.dumps(local_mock), 
            content_type = 'application/json',
            HTTP_ACCEPT = 'application/json',
            HTTP_AUTHORIZATION=self.auth
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(serviceAccount.objects.count(), 1)
        new_account = serviceAccount.objects.get(uuid=account.uuid)
        
        for field in ('uuid', 'name', 'plan_slug'):
            self.assertEqual(
                getattr(account, field), getattr(new_account, field)
            )

        self.assertEqual(None, new_account.expiration)


class TestUpdateAccount(TestActivateAccount):
    pass
