# -*- coding: utf-8 -*-
import logging

import requests
from django.conf import settings

from identity_client.utils import prepare_form_errors

# Imports a remover
import httplib2
import json

__all__ = ['APIClient']


class APIClient(object):

    api_host = settings.MYFC_ID['HOST']
    api_user = settings.MYFC_ID['CONSUMER_TOKEN'],
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
    def invoke_registration_api(cls, form):

        api_user = cls.api_user
        api_password = cls.api_password
        api_url = "%s/%s" % (
            cls.api_host,
            cls.registration_api
        )

        status_code = 500
        content = None
        error_dict = None

        registration_data = json.dumps(form.data)
        headers = {
            'content-type': 'application/json',
            'user-agent': 'myfc_id client',
            'cache-control': 'no-cache',
            'authorization': 'Basic {0}'.format('{0}:{1}'.format(api_user, api_password).encode('base64').strip()),
        }

        try:
            http = httplib2.Http()
            response, content = http.request(api_url,
                "POST", body=registration_data, headers=headers
            )

            status_code = response.status
            if status_code not in (200, 201):

                if status_code in (400, 409):
                    error_dict = json.loads(content)

                else:
                    raise Exception


        except (ValueError, httplib2.HttpLib2Error, Exception):
            # Caso o json esteja corrompido ou ocorra uma falha na comunicação com o servidor
            error_dict = {
                '__all__': [error_messages.get(status_code, error_messages['default']), ]
            }

        if error_dict:
            form._errors = prepare_form_errors(error_dict)

        return (status_code, content, form)


    @classmethod
    def fetch_user_accounts(cls, uuid):

        url = '{0}/organizations/api/identities/{1}/accounts/'.format(
            cls.api_host, uuid
        )

        accounts = error = None

        try:
            logging.info('fetch_user_accounts: Making request to %s', url)
            response = cls.pweb.get(url)
            response.raise_for_status()

            if response.status_code == 200:
                if response.text:
                    accounts = response.json()
                else:
                    accounts = []

            else:
                raise requests.exceptions.HTTPError('Unexpected response', response=response)
                
        except requests.exceptions.HTTPError as e:
            error = {
                'status': e.response.status_code,
                'message': e.response.text if e.response.text else e.message,
            }

        except requests.exceptions.ConnectionError as e:
            error = {
                'status': None,
                'message': 'Error connecting to PassaporteWeb',
            }

        except requests.exceptions.Timeout as e:
            error = {
                'status': None,
                'message': 'Timeout connecting to PassaporteWeb',
            }

        except (requests.exceptions.RequestException, Exception) as e:
            error = {
                'status': None,
                'message': u'Unexpected error: {0} <{1}>'.format(e, type(e)),
            }

        if error:
            logging.error(
                'fetch_user_accounts: Error making request: %s - %s',
                error['status'], error['message']
            )

        return accounts, error


    @classmethod
    def create_user_account(cls, uuid, name, plan_slug, expiration=None):
        api_user = cls.api_user
        api_password = cls.api_password

        http = httplib2.Http()
        url = '%s/%s' % (
            cls.api_host,
            'organizations/api/identities/{0}/accounts/'.format(uuid)
        )
        data = json.dumps({
            'name': name, 'plan_slug': plan_slug, 'expiration': expiration
        })
        headers = {
            'cache-control': 'no-cache',
            'content-length': str(len(data)),
            'content-type': 'application/json',
            'accept': 'application/json',
            'user-agent': 'myfc_id client',
            'authorization': 'Basic {0}'.format('{0}:{1}'.format(api_user, api_password).encode('base64').strip()),
        }

        account_data = None
        error = None

        try:
            response, content = http.request(url, "POST", headers=headers, body=data)
            if response.status in (200, 201):
                account_data = json.loads(content)

            else:
                error = {
                    'status': response.status,
                    'message': content,
                }

                logging.error(
                    'create_user_accounts: Error making request: %s - %s',
                    response.status, content,
                )

        except ValueError:
            error = {
                'status': response and response.status,
                'message': content,
            }

            logging.error(
                'create_user_accounts: Error making request: %s - %s',
                response, content,
            )

        except Exception, err:
            error = {
                'status': None,
                'message': u'unexpected error: ({0.__name__}) {1}'.format(type(err), err),
            }

            logging.error(
                'create_user_accounts: Error making request: %s, %s',
                err.__class__.__name__, err,
            )

        return account_data, error


    @classmethod
    def fetch_identity_data(cls, uuid=None, email=None):

        # Construir url da API
        api_host = cls.api_host
        api_user = cls.api_user
        api_password = cls.api_password
        api_path = cls.profile_api

        if not any((uuid, email)):
            raise ValueError("Either 'uuid' or 'email' must be given")
        elif uuid:
            api_uri = "%s/%s/%s" % (api_host, api_path, uuid)
        else:
            api_uri = "%s/%s/?email=%s" % (api_host, api_path, email)

        headers = {
            'content-type': 'application/json',
            'user-agent': 'myfc_id client',
            'cache-control': 'no-cache',
            'authorization': 'Basic {0}'.format('{0}:{1}'.format(api_user, api_password).encode('base64').strip()),
        }

        # Efetuar requisição
        http = httplib2.Http()
        response, content = http.request(api_uri, "GET", headers=headers)
        return (response.status, content)


    @classmethod
    def fetch_association_data(cls, api_path):

        # Construir url da API
        api_user = cls.api_user
        api_password = sels.api_password
        api_host = cls.api_host

        api_uri = "%s%s" % (api_host, api_path)

        headers = {
            'content-type': 'application/json',
            'user-agent': 'myfc_id client',
            'cache-control': 'no-cache',
            'authorization': 'Basic {0}'.format('{0}:{1}'.format(api_user, api_password).encode('base64').strip()),
        }

        # Efetuar requisição
        http = httplib2.Http()
        response, content = http.request(
            api_uri, "GET", headers=headers
        )
        return (response.status, content)


    @classmethod
    def update_user_api(cls, form, api_path):

        api_user = cls.api_user
        api_password = cls.api_password
        api_host = cls.api_host

        if api_path.startswith(api_host):
            api_url = api_path
        else:
            api_url = "%s%s" % (api_host, api_path)

        registration_data = json.dumps(form.data)
        headers = {
            'content-type':'application/json',
            'authorization': 'Basic {0}'.format('{0}:{1}'.format(api_user, api_password).encode('base64').strip()),
        }

        http = httplib2.Http()
        response, content = http.request(
            api_url, "PUT", body=registration_data, headers=headers
        )

        if response.status == 409:
            try:
                error_dict = json.loads(content)
            except ValueError:
                error_dict = {
                    '__all__': [error_messages.get(400, error_messages.get('default')), ]
                }

            form._errors = prepare_form_errors(error_dict)

        return (response.status, content, form)


error_messages = {
    401: u"Esta aplicação não está autorizada a utilizar o PassaporteWeb. Entre em contato com o suporte.",
    400: u"Erro na transmissão dos dados. Tente novamente.",
    409: u"Email já cadastrado.",
    'default': u"Erro no servidor. Entre em contato com o suporte.",
}
