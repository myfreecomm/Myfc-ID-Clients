# -*- coding: utf-8 -*-
from datetime import datetime as dt, timedelta

from identity_client.tests.helpers import MyfcIDTestCase as TestCase

from identity_client.models import Identity, ServiceAccount

__all__ = [
    'TestIdentityModel', 'TestServiceAccountModel'
]


class TestIdentityModel(TestCase):


    def setUp(self):
        self.email=u'teste@email.com'
        self.identity = Identity(
            first_name='Teste',
            last_name='Sobrenome',
            email=self.email,
            uuid='16fd2706-8baf-433b-82eb-8c7fada847da',
        )


    def test_unicode(self):
        # An Identity should always be authenticated
        self.assertEquals(unicode(self.identity), self.email)


    def test_always_authenticated(self):
        # An Identity should always be authenticated
        self.assertTrue(self.identity.is_authenticated())


    def test_never_anonymous(self):
        # An Identity should never be anonymous
        self.assertEquals(self.identity.is_anonymous(), False)


    def test_set_password_not_implemented(self):
        # This method should not be implemented
        self.assertRaises(
            NotImplementedError, 
            self.identity.set_password, 
            's3nH4'
        )


    def test_check_password_not_implemented(self):
        # This method should not be implemented
        self.assertRaises(
            NotImplementedError, 
            self.identity.check_password, 
            's3nH4'
        )


    def test_set_unusable_password_not_implemented(self):
        # This method should not be implemented
        self.assertRaises(
            NotImplementedError, 
            self.identity.set_unusable_password, 
        )



    def test_has_usable_password_always_false(self):
        # An Identity should never have a usable password
        self.assertEquals(self.identity.has_usable_password(), False)


class TestServiceAccountModel(TestCase):

    def setUp(self):
        self.email = u'teste@email.com'
        self.identity = Identity.objects.create(
            first_name = 'Teste',
            last_name = 'Sobrenome',
            email = self.email,
            uuid = '16fd2706-8baf-433b-82eb-8c7fada847da',
        )

        self.account_name = 'Test Account'
        self.account = ServiceAccount.objects.create(
            name = self.account_name,
            uuid = '16fd2706-8baf-433b-82eb-8c7fada847da',
            plan_slug = 'platinum-test-plan',
        )


    def test_unicode(self):
        # An Identity should always be authenticated
        self.assertEquals(unicode(self.account), self.account_name)


    def test_account_without_expiration_is_active(self):
        self.assertEqual(self.account.expiration, None)
        self.assertTrue(self.account.is_active)


    def test_account_with_expiration_in_the_future_is_active(self):
        self.account.expiration = dt.today() + timedelta(days=2)
        self.assertTrue(self.account.is_active)


    def test_account_with_expiration_in_the_past_is_not_active(self):
        self.account.expiration = dt.today() - timedelta(days=2)
        self.assertFalse(self.account.is_active)


    def test_default_members_count_is_zero(self):
        self.assertEqual(self.account.members_count, 0)


    def test_add_member_to_empty_account(self):
        self.account.add_member(self.identity, roles=['user'])
        self.assertEqual(self.account.members_count, 1)


    def test_add_member_who_is_already_a_member_does_not_change_member_count(self):
        self.account.add_member(self.identity, roles=['user'])
        self.account.add_member(self.identity, roles=['user', 'admin'])
        self.assertEqual(self.account.members_count, 1)


    def test_get_member_returns_accountmember(self):
        self.account.add_member(self.identity, roles=['user'])
        member = self.account.get_member(self.identity)
        self.assertEqual(member.identity, self.identity)
        self.assertEqual(member.roles, ['user'])


    def test_get_non_existing_member_returns_none(self):
        member = self.account.get_member(self.identity)
        self.assertEqual(member, None)


    def test_get_member_roles_is_a_list_of_strings(self):
        self.account.add_member(self.identity, roles=['user', 'admin'])
        member = self.account.get_member(self.identity)
        self.assertEqual(member.roles, ['admin', 'user'])


    def test_add_member_who_is_already_a_member_overwrites_roles(self):
        self.account.add_member(self.identity, roles=['user'])
        self.account.add_member(self.identity, roles=['user', 'admin'])
        member = self.account.get_member(self.identity)
        self.assertEqual(member.roles, ['admin', 'user'])


    def test_member_may_have_no_roles(self):
        self.account.add_member(self.identity, roles=[])
        member = self.account.get_member(self.identity)
        self.assertEqual(member.roles, [])


    def test_remove_member_returns_account(self):
        self.account.add_member(self.identity, roles=['user'])
        account = self.account.remove_member(self.identity)
        self.assertEqual(account, self.account)
        self.assertEqual(account.members_count, 0)


    def test_remove__non_existing_member_fails_silently(self):
        account = self.account.remove_member(self.identity)
        self.assertEqual(account, self.account)
        self.assertEqual(account.members_count, 0)


    def test_account_without_expiration_is_active(self):
        self.assertEqual(self.account.expiration, None)
        active_accounts = ServiceAccount.active().all()
        self.assertEqual(len(active_accounts), 1)
        self.assertEqual(active_accounts[0], self.account)


    def test_account_with_expiration_in_the_future_is_active(self):
        self.account.expiration = dt.today() + timedelta(days=2)
        self.account.save()
        active_accounts = ServiceAccount.active().all()
        self.assertEqual(len(active_accounts), 1)
        self.assertEqual(active_accounts[0], self.account)


    def test_account_with_expiration_in_the_past_is_not_active(self):
        self.account.expiration = dt.today() - timedelta(days=2)
        self.account.save()
        active_accounts = ServiceAccount.active().all()
        self.assertEqual(len(active_accounts), 0)


    def test_accounts_for_identity(self):
        self.account.add_member(self.identity, roles=['user'])
        active_accounts = ServiceAccount.for_identity(self.identity)
        self.assertEqual(len(active_accounts), 1)
        self.assertEqual(active_accounts[0], self.account)


    def test_accounts_for_identity_without_accounts_associated(self):
        active_accounts = ServiceAccount.for_identity(self.identity)
        self.assertEqual(len(active_accounts), 0)


    def test_accounts_for_identity_ignores_expired_accounts_by_default(self):
        self.account.expiration = dt.today() - timedelta(days=2)
        self.account.add_member(self.identity, roles=[])

        active_accounts = ServiceAccount.for_identity(self.identity)
        self.assertEqual(len(active_accounts), 0)


    def test_accounts_for_identity_may_include_expired_accounts(self):
        self.account.expiration = dt.today() - timedelta(days=2)
        self.account.add_member(self.identity, roles=[])

        active_accounts = ServiceAccount.for_identity(self.identity, include_expired=True)
        self.assertEqual(len(active_accounts), 1)
        self.assertEqual(active_accounts[0], self.account)
