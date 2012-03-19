# -*- coding: utf-8 -*-
import json
from datetime import datetime as dt, timedelta
from uuid import uuid4
from collections import namedtuple

from django.conf import settings
from django.core.urlresolvers import reverse, NoReverseMatch

from identity_client.tests.helpers import MyfcIDTestCase as TestCase

from identity_client.models import Identity
from identity_client.utils import get_account_module


__all__ = ['TestActivateAccount', 'TestUpdateAccount']

EXPIRATION_FORMAT = '%Y-%m-%d %H:%M:%S'

RemoteAccount = namedtuple('RemoteAccount', [
    'uuid', 'name', 'service_name', 'service_slug', 'plan_slug', 'expiration', 'add_member_url'
])

account = RemoteAccount(
    uuid = '16fd2706-8baf-433b-82eb-8c7fada847da',
    name = 'Pessoal',
    service_name = 'Identity Client',
    service_slug = 'identity_client',
    plan_slug = 'plus',
    expiration = (dt.today() + timedelta(days=1)).strftime(EXPIRATION_FORMAT),
    add_member_url = 'http://192.168.1.48:8000/organizations/api/accounts/b39bad59-94af-4880-995a-04967b454c7a/members',
)

dict_mock = {
    u'account_data': {u'name': account.name, u'uuid': account.uuid},
    u'members_data': [],
    u'expiration': account.expiration,
    u'service_data': {u'name': account.service_name, u'slug': account.service_slug},
    u'plan_slug': account.plan_slug,
    u'add_member_url': account.add_member_url,
    u'members_data': [
        {
            u'identity': u'f55afb82-e63b-11e0-b300-574391ce2a7a',
            u'roles': ['owner'],
            u'membership_details_url': u'http://testserver/organizations/api/accounts/2067c5e6-5b77-434d-a43c-abfb24981f93/members/e57448c4-41e6-483b-872a-9f32fd15cd63/',
        },
        {
            u'identity': u'f55afb82-e63b-11e0-b300-574391ce2a7b',
            u'roles': ['user'],
            u'membership_details_url': u'http://testserver/organizations/api/accounts/2067c5e6-5b77-434d-a43c-abfb24981f93/members/e57448c4-41e6-483b-872a-9f32fd15cd6d/',
        },
    ],
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


    def test_response_format(self):
        response = self.client.put(self.url, 
            json.dumps(dict_mock), 
            content_type = 'application/json',
            HTTP_ACCEPT = 'application/json',
            HTTP_AUTHORIZATION=self.auth
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data, {
            u'expiration': account.expiration,
            u'is_active': True,
            u'name': u'Pessoal',
            u'uuid': u'16fd2706-8baf-433b-82eb-8c7fada847da'
        })


    def test_response_format(self):
        response = self.client.put(self.url, 
            json.dumps(dict_mock), 
            content_type = 'application/json',
            HTTP_ACCEPT = 'application/xml',
            HTTP_AUTHORIZATION=self.auth
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 
            '<?xml version="1.0" encoding="utf-8"?>\n<root><expiration>%s</expiration><is_active>True</is_active><uuid>16fd2706-8baf-433b-82eb-8c7fada847da</uuid><name>Pessoal</name></root>' % account.expiration
        )


    def test_creates_account_on_success(self):
        response = self.client.put(self.url, 
            json.dumps(dict_mock), 
            content_type = 'application/json',
            HTTP_ACCEPT = 'application/json',
            HTTP_AUTHORIZATION=self.auth
        )

        self.assertEqual(response.status_code, 200)

        serviceAccount =  get_account_module()
        self.assertEqual(serviceAccount.objects.count(), 1)
        new_account = serviceAccount.objects.get(uuid=account.uuid)
        
        for field in ('uuid', 'name', 'plan_slug'):
            self.assertEqual(
                getattr(account, field), getattr(new_account, field)
            )

        self.assertEqual(
            account.expiration, new_account.expiration.strftime(EXPIRATION_FORMAT)
        )


    def test_creates_account_without_expiration(self):
        local_mock = dict_mock.copy()
        local_mock['expiration'] = None

        response = self.client.put(self.url, 
            json.dumps(local_mock), 
            content_type = 'application/json',
            HTTP_ACCEPT = 'application/json',
            HTTP_AUTHORIZATION=self.auth
        )

        self.assertEqual(response.status_code, 200)

        serviceAccount =  get_account_module()
        self.assertEqual(serviceAccount.objects.count(), 1)
        new_account = serviceAccount.objects.get(uuid=account.uuid)
        
        for field in ('uuid', 'name', 'plan_slug'):
            self.assertEqual(
                getattr(account, field), getattr(new_account, field)
            )

        self.assertEqual(None, new_account.expiration)


    def test_updates_account_members_on_success(self):
        response = self.client.put(self.url, 
            json.dumps(dict_mock), 
            content_type = 'application/json',
            HTTP_ACCEPT = 'application/json',
            HTTP_AUTHORIZATION=self.auth
        )

        self.assertEqual(response.status_code, 200)

        serviceAccount =  get_account_module()
        self.assertEqual(serviceAccount.objects.count(), 1)
        new_account = serviceAccount.objects.get(uuid=account.uuid)
        
        self.assertEqual(new_account.members_count, 2)
        


class TestUpdateAccount(TestActivateAccount):

    def setUp(self):
        super(TestUpdateAccount, self).setUp()
        self.default_plan = 'previous_plan'
        self.default_expiration = None

        serviceAccount = get_account_module()

        self.previous_user = Identity.objects.create(
            uuid='f55afb82-e63b-11e0-b300-574391ce2a7a', email='user@test.com'
        )
        self.previous_account = serviceAccount.objects.create(
            uuid = account.uuid,
            name = account.name,
            plan_slug = self.default_plan,
            expiration =  self.default_expiration,
        )
        self.previous_account.add_member(self.previous_user, [])
        self.previous_account.save()

    def test_does_not_create_a_new_account(self):
        response = self.client.put(self.url, 
            json.dumps(dict_mock), 
            content_type = 'application/json',
            HTTP_ACCEPT = 'application/json',
            HTTP_AUTHORIZATION=self.auth
        )

        self.assertEqual(response.status_code, 200)

        serviceAccount =  get_account_module()
        self.assertEqual(serviceAccount.objects.count(), 1)

    def test_activation_works_as_plan_change(self):
        response = self.client.put(self.url, 
            json.dumps(dict_mock), 
            content_type = 'application/json',
            HTTP_ACCEPT = 'application/json',
            HTTP_AUTHORIZATION=self.auth
        )

        self.assertEqual(response.status_code, 200)

        serviceAccount =  get_account_module()
        self.assertEqual(serviceAccount.objects.count(), 1)
        new_account = serviceAccount.objects.get(uuid=account.uuid)
        
        self.assertNotEqual(self.default_plan, new_account.plan_slug)
        self.assertEqual(account.plan_slug, new_account.plan_slug)

    def test_activation_updates_expiration_date(self):
        response = self.client.put(self.url, 
            json.dumps(dict_mock), 
            content_type = 'application/json',
            HTTP_ACCEPT = 'application/json',
            HTTP_AUTHORIZATION=self.auth
        )

        self.assertEqual(response.status_code, 200)

        serviceAccount =  get_account_module()
        self.assertEqual(serviceAccount.objects.count(), 1)
        new_account = serviceAccount.objects.get(uuid=account.uuid)
        
        self.assertNotEqual(self.default_expiration, new_account.expiration)
        self.assertEqual(
            account.expiration, new_account.expiration.strftime(EXPIRATION_FORMAT)
        )

    def test_updates_account_members_on_success(self):
        member = self.previous_account.get_member(self.previous_user)
        self.assertEqual(member.roles, [])

        response = self.client.put(self.url, 
            json.dumps(dict_mock), 
            content_type = 'application/json',
            HTTP_ACCEPT = 'application/json',
            HTTP_AUTHORIZATION=self.auth
        )

        self.assertEqual(response.status_code, 200)

        serviceAccount =  get_account_module()
        self.assertEqual(serviceAccount.objects.count(), 1)
        new_account = serviceAccount.objects.get(uuid=account.uuid)
        
        self.assertEqual(new_account.members_count, 2)
        member = new_account.get_member(self.previous_user)
        self.assertEqual(member.roles, ['owner'])

    def test_removes_stale_account_members_on_success(self):
        member = self.previous_account.get_member(self.previous_user)
        self.assertEqual(member.roles, [])

        local_mock = dict_mock.copy()
        local_mock['members_data'] = {}

        response = self.client.put(self.url, 
            json.dumps(local_mock), 
            content_type = 'application/json',
            HTTP_ACCEPT = 'application/json',
            HTTP_AUTHORIZATION=self.auth
        )

        self.assertEqual(response.status_code, 200)

        serviceAccount =  get_account_module()
        new_account = serviceAccount.objects.get(uuid=account.uuid)
        self.assertEqual(new_account.members_count, 0)
