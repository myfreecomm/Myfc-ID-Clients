# -*- coding: utf-8 -*-

from django.test import TestCase

from identity_auth_client.models import Identity

__all__ = ['TestIdentityModel', ]


class TestIdentityModel(TestCase):


    def setUp(self):
        self.email=u'teste@email.com'
        self.identity = Identity(
            first_name='Teste',
            last_name='Sobrenome',
            email=self.email,
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
