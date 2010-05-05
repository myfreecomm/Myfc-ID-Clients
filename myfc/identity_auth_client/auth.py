# -*- coding: utf-8 -*-
import urllib2
import json
from django.contrib.auth.models import AnonymousUser
from django.conf import settings

from models import Identity


class MyfcidAPIBackend(object):
    """
    Authenticates a user using the Myfc ID API.
    """

    def authenticate(self, email=None, password=None):
        identity = None

        # Fetch user data 
        response_content = self.fetch_user_data(email, password)

        if response_content:
            # Deserialize data
            user_data = json.loads(response_content)

            # Create an updated Identity instance for this user
            identity, created = Identity.objects.get_or_create(email=user_data['email'])
            self._update_user(identity, user_data)

            # Set this user's backend 
            identity.backend = "%s.%s" % (MyfcidAPIBackend.__module__, 'MyfcidAPIBackend')

        return identity
            

    def get_user(self, user_id):
        return Identity.objects.get(userid)


    def _update_user(self, user, user_data):
        user.first_name = user_data['first_name']
        user.last_name = user_data['last_name']
        user.save()


    def fetch_user_data(self, user, password):

        def setup_urlopener(uri, user, password):
            passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
            passman.add_password(None, uri, user, password)
            authhandler = urllib2.HTTPBasicAuthHandler(passman)
            opener = urllib2.build_opener(authhandler)
            urllib2.install_opener(opener)

        # Build the API uri
        uri = '%s/%s' % (settings.AUTH_API['HOST'], settings.AUTH_API['PATH'])

        # Setup an url opener to handle authentication
        opener = setup_urlopener(uri, user, password)

        # Request the data
        handle = urllib2.urlopen(uri)
        status_code = handle.getcode()

        # If the request is successful, read response data
        if status_code == 200:
            response_content = handle.read()
        else:
            response_content = None

        handle.close()
        
        return response_content

    
def get_user(userid=None):
    """
    Returns a User object from an id (User.id). Django's equivalent takes
    request, but taking an id instead leaves it up to the developer to store
    the id in any way they want (session, signed cookie, etc.)
    """
    if not userid:
        return AnonymousUser()
    return MyfcidAPIBackend().get_user(userid) or AnonymousUser()
