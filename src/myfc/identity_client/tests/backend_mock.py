# -*- coding: utf-8 -*-
from uuid import uuid4

from django.contrib.auth.models import AnonymousUser

from identity_client.models import Identity


class MyfcidAPIBackendMock(object):
    """
    Mocks the Myfc ID API user authentication
    """

    def authenticate(self, email=None, password=None, **kwargs):

        identity = Identity.objects.create(
            uuid=str(uuid4()), email=email
        )

        # Set this user's backend
        identity.backend = "%s.%s" % (MyfcidAPIBackendMock.__module__,
                                     'MyfcidAPIBackendMock')

        # Append additional user data to a temporary attribute
        identity.user_data = kwargs

        return identity


    def get_user(self, user_id):
        try:
            user = Identity.objects.get(id=user_id)
        except Identity.DoesNotExist:
            user = None

        return user


def get_user(userid=None):
    """
    Returns a User object from an id (User.id). Django's equivalent takes
    request, but taking an id instead leaves it up to the developer to store
    the id in any way they want (session, signed cookie, etc.)
    """
    if not userid:
        return AnonymousUser()
    return MyfcidAPIBackendMock().get_user(userid) or AnonymousUser()
