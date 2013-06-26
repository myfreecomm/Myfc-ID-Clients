# -*- coding: utf-8 -*-
import logging
import json

import requests
from django.conf import settings

from identity_client.decorators import handle_api_exceptions, handle_api_exceptions_with_form

__all__ = ['APIClient']

# TODO: 
# - fetch_application_accounts
# - atualizar informações de uma conta


class APIClient(object):

    api_host = settings.MYFC_ID['HOST']
    api_user = settings.MYFC_ID['CONSUMER_TOKEN']
    api_password = settings.MYFC_ID['CONSUMER_SECRET']
    profile_api = settings.MYFC_ID['PROFILE_API']
    registration_api = settings.MYFC_ID['REGISTRATION_API']

    pweb = requests.Session()
    pweb.auth = (api_user, api_password)
    pweb.headers.update({
        'cache-control': 'no-cache',
        'content-length': '0',
        'content-type': 'application/json',
        'accept': 'application/json',
        'user-agent': 'myfc_id client',
    })

    @classmethod
    @handle_api_exceptions_with_form
    def invoke_registration_api(cls, form):

        url = "{0}/{1}".format(cls.api_host, cls.registration_api)

        logging.info('invoke_registration_api: Making request to %s', url)

        registration_data = json.dumps(form.data)
        response = cls.pweb.post(
            url,
            headers={'content-length': str(len(registration_data))},
            data=registration_data
        )

        if response.status_code not in (200, 201):
            response.raise_for_status()
            raise requests.exceptions.HTTPError('Unexpected response', response=response)

        return response.status_code, response.json()


    @classmethod
    @handle_api_exceptions
    def fetch_identity_data(cls, uuid=None, email=None):

        if not any((uuid, email)):
            raise ValueError("Either 'uuid' or 'email' must be given")
        elif uuid:
            url = "{0}/{1}/{2}/".format(cls.api_host, cls.profile_api, uuid)
        else:
            url = "{0}/{1}/?email={2}".format(cls.api_host, cls.profile_api, email)

        logging.info('fetch_identity_data: Making request to %s', url)

        response = cls.pweb.get(url)

        if response.status_code != 200:
            response.raise_for_status()
            raise requests.exceptions.HTTPError('Unexpected response', response=response)

        return response.status_code, response.json()


    @classmethod
    @handle_api_exceptions_with_form
    def update_user_api(cls, form, api_path):

        if api_path.startswith(cls.api_host):
            url = api_path
        else:
            url = "{0}{1}".format(cls.api_host, api_path)

        logging.info('update_user_api: Making request to %s', url)

        user_data = json.dumps(form.data)
        response = cls.pweb.put(
            url,
            headers={'content-length': str(len(user_data))},
            data=user_data
        )

        if response.status_code != 200:
            response.raise_for_status()
            raise requests.exceptions.HTTPError('Unexpected response', response=response)

        return response.status_code, response.json()


    @classmethod
    @handle_api_exceptions
    def fetch_association_data(cls, api_path):

        if api_path.startswith(cls.api_host):
            url = api_path
        else:
            url = "{0}{1}".format(cls.api_host, api_path)

        logging.info('fetch_association_data: Making request to %s', url)
        response = cls.pweb.get(url)

        if response.status_code != 200:
            response.raise_for_status()
            raise requests.exceptions.HTTPError('Unexpected response', response=response)

        return response.status_code, response.json()


    @classmethod
    @handle_api_exceptions
    def update_association_data(cls, new_data, api_path):

        if api_path.startswith(cls.api_host):
            url = api_path
        else:
            url = "{0}{1}".format(cls.api_host, api_path)

        logging.info('update_association_data: Making request to %s', url)

        association_data = json.dumps(new_data)
        response = cls.pweb.put(
                url,
                headers={'content-length': str(len(association_data))},
                data=association_data
        )

        if response.status_code != 200:
            response.raise_for_status()
            raise requests.exceptions.HTTPError('Unexpected response', response=response)

        return response.status_code, response.json()


    @classmethod
    @handle_api_exceptions
    def fetch_user_accounts(cls, uuid, include_expired_accounts=False):

        url = '{0}/organizations/api/identities/{1}/accounts/'.format(cls.api_host, uuid)

        logging.info('fetch_user_accounts: Making request to %s', url)
        response = cls.pweb.get(url, params={
            'include_expired_accounts': include_expired_accounts,
        })

        if response.status_code != 200:
            response.raise_for_status()
            raise requests.exceptions.HTTPError('Unexpected response', response=response)

        return response.status_code, response.json()
                

    @classmethod
    @handle_api_exceptions
    def create_user_account(cls, uuid, plan_slug, account_uuid=None, account_name=None, expiration=None):

        account_data = {'plan_slug': plan_slug, 'expiration': expiration}
        if account_uuid:
            account_data['uuid'] = account_uuid
        elif account_name:
            account_data['name'] = account_name
        else:
            raise ValueError("Either 'account_uuid' or 'account_name' must be given")

        account_data = json.dumps(account_data)

        url = '{0}/organizations/api/identities/{1}/accounts/'.format(cls.api_host, uuid)
        logging.info('create_user_account: Making request to %s', url)

        response = cls.pweb.post(
            url,
            headers={'content-length': str(len(account_data))},
            data=account_data
        )

        if response.status_code not in (200, 201):
            response.raise_for_status()
            raise requests.exceptions.HTTPError('Unexpected response', response=response)

        return response.status_code, response.json()


    @classmethod
    @handle_api_exceptions
    def fetch_account_data(cls, account_uuid):

        url = '{0}/organizations/api/accounts/{1}/'.format(cls.api_host, account_uuid)

        logging.info('fetch_account_data: Making request to %s', url)
        response = cls.pweb.get(url)

        if response.status_code != 200:
            response.raise_for_status()
            raise requests.exceptions.HTTPError('Unexpected response', response=response)

        return response.status_code, response.json()


    @classmethod
    @handle_api_exceptions
    def add_account_member(cls, user_uuid, roles, api_path):

        if not isinstance(roles, list):
            raise TypeError(u"roles must be a list")

        member_data = json.dumps({'identity': user_uuid, 'roles': roles})

        if api_path.startswith(cls.api_host):
            url = api_path
        else:
            url = "{0}{1}".format(cls.api_host, api_path)

        logging.info('add_account_member: Making request to %s', url)

        response = cls.pweb.post(
            url,
            headers={'content-length': str(len(member_data))},
            data=member_data
        )

        if response.status_code not in (200, 201):
            response.raise_for_status()
            raise requests.exceptions.HTTPError('Unexpected response', response=response)

        return response.status_code, response.json()


    @classmethod
    @handle_api_exceptions
    def update_member_roles(cls, roles, api_path):

        if not isinstance(roles, list):
            raise TypeError(u"roles must be a list")

        member_data = json.dumps({'roles': roles})

        if api_path.startswith(cls.api_host):
            url = api_path
        else:
            url = "{0}{1}".format(cls.api_host, api_path)

        logging.info('update_member_roles: Making request to %s', url)

        response = cls.pweb.put(
            url,
            headers={'content-length': str(len(member_data))},
            data=member_data
        )

        if response.status_code != 200:
            response.raise_for_status()
            raise requests.exceptions.HTTPError('Unexpected response', response=response)

        return response.status_code, response.json()


    @classmethod
    @handle_api_exceptions
    def remove_account_member(cls, api_path):

        if api_path.startswith(cls.api_host):
            url = api_path
        else:
            url = "{0}{1}".format(cls.api_host, api_path)

        logging.info('remove_account_member: Making request to %s', url)

        response = cls.pweb.delete(url)

        if response.status_code != 204:
            response.raise_for_status()
            raise requests.exceptions.HTTPError('Unexpected response', response=response)

        return response.status_code, response.text
