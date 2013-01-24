# -*- coding: utf-8 -*-
from datetime import datetime as dt
from collections import namedtuple

from mongoengine import Document, EmbeddedDocument, queryset

from django.conf import settings
from djangorestframework import status
from djangorestframework.views import View
from djangorestframework.resources import Resource
from djangorestframework.authentication import BaseAuthentication
from djangorestframework.permissions import IsAuthenticated
from djangorestframework.response import ErrorResponse

from requestlogging import logging
from identity_client.utils import get_account_module
from identity_client.models import Identity


__all__ = ['AccountActivationView', ]


Consumer = namedtuple('Consumer', ['token', 'secret', 'is_authenticated', 'username'])


class AccountActivationAuthenticator(BaseAuthentication):

    def authenticate(self, request):
        expected_token = settings.ACTIVATION_API['TOKEN']
        expected_secret = settings.ACTIVATION_API['SECRET']
        token, secret = self._get_authorization(request)

        return Consumer(
            token=token, 
            secret=secret, 
            username=token,
            is_authenticated=lambda: bool((token, secret) == (expected_token, expected_secret)),
        )

    def _get_authorization(self, request):
        """ 
        Extracts the credentials supplied on the HTTP_AUTHORIZATION header
        """
        header = request.META.get('HTTP_AUTHORIZATION')
        if header and header.startswith('Basic '):
            try:
                auth_string = header[6:].decode('base64')
                user, passwd = auth_string.split(':', 1)
                return user, passwd
            except:
                logging.error('parsing (header = %s) - %s: %s',
                    header, type(e).__name__, e)
                
        else:
            logging.debug('unparsable authorizarion header: %s', header)
                
        return None, None


class AccountResource(Resource):

    fields = ('uuid', 'name', 'expiration', 'is_active')

    def serialize(self, obj):

        if isinstance(obj, (Document, EmbeddedDocument)):
            return self.serialize_model(obj)

        elif isinstance(obj, (queryset.QuerySet, )):
            return self.serialize_iter(obj)

        else:
            return super(AccountResource, self).serialize(obj)

    def serialize_val(self, key, obj):
        if isinstance(obj, (list, tuple)):
            return [self.serialize_val(key, v) for v in obj]

        elif isinstance(obj, (dict, )):
            return dict(
                (k, self.serialize_val(k, v))
                for k, v in obj.iteritems()
            )

        elif hasattr(obj, 'as_dict'):
            return self.serialize_val(key, obj.as_dict())

        elif isinstance(obj, (EmbeddedDocument, Document)):
            return self.serialize_val(key, dict(
                (k, getattr(obj, k)) for k, v in obj._fields.iteritems()
            ))

        else:
            return super(AccountResource, self).serialize_val(key, obj)


class AccountActivationView(View):

    resource = AccountResource
    authentication = (AccountActivationAuthenticator,)
    permissions = (IsAuthenticated, )


    def get_request_data(self):
        content = self.CONTENT or {}

        try:
            data = dict(self.DATA)

            if data['expiration'] is None:
                expiration = None
            else:
                expiration = dt.strptime(data['expiration'], '%Y-%m-%d %H:%M:%S')

            result = {
                'uuid': data['account_data']['uuid'],
                'name': data['account_data']['name'],
                'service_slug': data['service_data']['slug'],
                'service_name': data['service_data']['name'],
                'plan_slug': data['plan_slug'],
                'expiration': expiration,
                'members_data': data.get('members_data', {})
            }

        except KeyError, e:
            message = {
                'errors': [u'Not enought data for activation.'],
                'field-errors': {e.args[0]: [u'This field is required.']}
            }
            raise ErrorResponse(status.HTTP_400_BAD_REQUEST, content=message)

        return result


    def put(self, request, uuid):
        try:
            logging.info(u"Account activation called by consumer with token %s.",
                request.user, request=request
            )

            data = self.get_request_data()

            serviceAccount = get_account_module()
            try:
                account = serviceAccount.objects.get(uuid=data['uuid'])
            except serviceAccount.DoesNotExist:
                account = serviceAccount(uuid=data['uuid'])

            account.name = data['name']
            account.plan_slug = data['plan_slug']
            account.expiration = data['expiration']

            account.clear_members()
            for item in data['members_data']:
                identity, created = Identity.objects.get_or_create(uuid=item['identity'])
                account.add_member(identity, item['roles'])

            account.save()

        except ErrorResponse, e:
            message = u"Bad request. Errors: %s" % e.response.cleaned_content
            logging.error(message, request=request)
            raise

        except Exception, e:
            message = u"Unknown error during activation: Request data is %s" % (data)
            logging.error(message, request=request)
            raise ErrorResponse(status.HTTP_500_INTERNAL_SERVER_ERROR, content=message)

        return account
