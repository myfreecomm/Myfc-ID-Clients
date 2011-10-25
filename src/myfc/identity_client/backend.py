# -*- coding: utf-8 -*-
import json
import httplib2
from django.contrib.auth.models import AnonymousUser
from django.conf import settings

from identity_client.models import Identity
from identity_client.signals import pre_identity_authentication


class MyfcidAPIBackend(object):
    """
    Authenticates a user using the Myfc ID API.
    """

    def authenticate(self, email=None, password=None):
        identity = None

        # Fetch user data
        response_content = self.fetch_user_data(email, password)

        # Deserialize data
        try:
            user_data = json.loads(response_content)
        except (TypeError, ValueError):
            user_data = None

        if user_data:
            identity = self.create_local_identity(user_data)

        return identity


    def create_local_identity(self, user_data):
         # Create an updated Identity instance for this user
        identity, created = Identity.objects.get_or_create(uuid=user_data['uuid'])
        self._update_user(identity, user_data)

        # Set this user's backend
        identity.backend = "%s.%s" % (MyfcidAPIBackend.__module__, 'MyfcidAPIBackend')

        # Append additional user data to a temporary attribute
        identity.user_data = user_data

        pre_identity_authentication.send_robust(
            sender="identity_client.MyfcidAPIBackend.backend",
            identity = identity,
            user_data = user_data,
        )
        return identity


    def get_user(self, user_id):
        try:
            user = Identity.objects.get(id=user_id)
        except Exception:
            user = None

        return user


    def _update_user(self, user, user_data):
        user.email = user_data['email']
        user.first_name = user_data['first_name']
        user.last_name = user_data['last_name']
        user.is_active = user_data['is_active']
        user.save()


    def fetch_user_data(self, user, password):

        # Build the API uri
        uri = '%s/%s' % (
            settings.MYFC_ID['HOST'],
            settings.MYFC_ID['AUTH_API'],
        )

        # Setup httplib2 for this request
        h = httplib2.Http()
        h.add_credentials(user, password)

        # Request the data
        try:
            response, content = h.request(
                uri, method='GET',
                headers={
                    'content-type': 'application/json',
                    'cache-control': 'no-cache',
                    'user-agent': 'myfc_id client'
                }
            )

            # If the request is successful, read response data
            if response.status != 200:
                raise ValueError

            response_content = content
        except (ValueError, AttributeError, httplib2.HttpLib2Error):
            response_content = None

        return response_content


class AccountManagerAPIBackend(object):

    def fetch_user_accounts(self, uuid):
        api_user = settings.MYFC_ID['CONSUMER_TOKEN']
        api_password = settings.MYFC_ID['CONSUMER_SECRET']

        http = httplib2.Http()
        url = '%s/%s' % (
            settings.MYFC_ID['HOST'],
            'organizations/api/identities/{0}/accounts'.format(uuid)
        )
        headers = {
            'cache-control': 'no-cache',
            'content-length': '0',
            'content-type': 'application/json',
            'user-agent': 'myfc_id client',
            'authorization': 'Basic {0}'.format('{0}:{1}'.format(api_user, api_password).encode('base64').strip()),
            }

        response = content = error = None
        accounts = []

        try:
            response, content = http.request(url, "GET", headers=headers)
            accounts = json.loads(content)

        except ValueError:
            error = {
                'status': response and response.status,
                'message': content,
            }

        except httplib2.HttpLib2Error, err:
            error = {
                'status': None,
                'message': u'connection error: {0}'.format(err),
            }

        except Exception, err:
            error = {
                'status': None,
                'message': u'unexpected error: ({0.__name__}) {1}'.format(type(err), err),
            }

        return accounts, error


def get_user(userid=None):
    """
    Returns a User object from an id (User.id). Django's equivalent takes
    request, but taking an id instead leaves it up to the developer to store
    the id in any way they want (session, signed cookie, etc.)
    """
    if not userid:
        return AnonymousUser()
    return MyfcidAPIBackend().get_user(userid) or AnonymousUser()


def get_user_accounts(userid=None):
    if not userid:
        return []
    return AccountManagerAPIBackend().fetch_user_accounts(userid)
