# -*- coding: utf-8 -*-
import logging
import json
import requests

from django.conf import settings

from identity_client.utils import prepare_form_errors

__all__ = ['APIClient']

# TODO: 
#   - DRY (tratamento de exceções, etc)
#   - compatibilizar retorno das operações da api
#   - create_user_account usando uuid
#   - fetch_application_accounts
#   - operacoes que o ecommerce precisa
#   - listar membros de uma conta
#   - adicionar membro a uma conta
#   - alterar papelis de um membro de uma conta
#   - remover membro a uma conta


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
    def invoke_registration_api(cls, form):

        status_code = 500
        content = error = error_dict = None

        url = "{0}/{1}".format(cls.api_host, cls.registration_api)

        try:
            registration_data = json.dumps(form.data)

            logging.info('invoke_registration_api: Making request to %s', url)
            response = cls.pweb.post(url, headers={'content-length': str(len(registration_data))}, data=registration_data)
            status_code = response.status_code

            if status_code in (200, 201):
                content = response.json()
            else:
                response.raise_for_status()
                raise requests.exceptions.HTTPError('Unexpected response', response=response)

        except requests.exceptions.HTTPError as e:
            if e.response.status_code in (400, 409):
                error_dict = e.response.json()
            else:
                error_dict = {
                    '__all__': [error_messages.get(e.response.status_code, error_messages['default']), ]
                }

            error = {
                'status': e.response.status_code,
                'message': e.response.text if e.response.text else e.message,
            }

        except requests.exceptions.ConnectionError as e:
            error_dict = {
                '__all__': [error_messages.get('ConnectionError', error_messages['default']), ]
            }
            error = {
                'status': None,
                'message': 'Error connecting to PassaporteWeb',
            }

        except requests.exceptions.Timeout as e:
            error_dict = {
                '__all__': [error_messages.get('Timeout', error_messages['default']), ]
            }
            error = {
                'status': None,
                'message': 'Timeout connecting to PassaporteWeb',
            }

        except (requests.exceptions.RequestException, Exception) as e:
            error_dict = {
                '__all__': [error_messages.get('default'), ]
            }
            error = {
                'status': None,
                'message': u'Unexpected error: {0} <{1}>'.format(e, type(e)),
            }

        if error_dict:
            form._errors = prepare_form_errors(error_dict)

        if error:
            logging.error(
                'invoke_registration_api: Error making request: %s - %s',
                error['status'], error['message']
            )

        return (status_code, content, form)


    @classmethod
    def fetch_identity_data(cls, uuid=None, email=None):

        if not any((uuid, email)):
            raise ValueError("Either 'uuid' or 'email' must be given")
        elif uuid:
            url = "{0}/{1}/{2}/".format(cls.api_host, cls.profile_api, uuid)
        else:
            url = "{0}/{1}/?email={2}".format(cls.api_host, cls.profile_api, email)

        status_code = 500
        content = error = None

        try:
            logging.info('fetch_identity_data: Making request to %s', url)
            response = cls.pweb.get(url)
            status_code = response.status_code

            if response.status_code == 200:
                content = response.json()

            else:
                response.raise_for_status()
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
                'fetch_identity_data: Error making request: %s - %s',
                error['status'], error['message']
            )

        return status_code, content, error


    @classmethod
    def update_user_api(cls, form, api_path):

        status_code = 500
        content = error = error_dict = None

        if api_path.startswith(cls.api_host):
            url = api_path
        else:
            url = "{0}{1}".format(cls.api_host, api_path)

        try:
            registration_data = json.dumps(form.data)

            logging.info('update_user_api: Making request to %s', url)
            response = cls.pweb.put(url, headers={'content-length': str(len(registration_data))}, data=registration_data)
            status_code = response.status_code

            if status_code == 200:
                content = response.json()
            else:
                response.raise_for_status()
                raise requests.exceptions.HTTPError('Unexpected response', response=response)

        except requests.exceptions.HTTPError as e:
            if e.response.status_code in (400, 409):
                error_dict = e.response.json()
            else:
                error_dict = {
                    '__all__': [error_messages.get(e.response.status_code, error_messages['default']), ]
                }

            error = {
                'status': e.response.status_code,
                'message': e.response.text if e.response.text else e.message,
            }

        except requests.exceptions.ConnectionError as e:
            error_dict = {
                '__all__': [error_messages.get('ConnectionError', error_messages['default']), ]
            }
            error = {
                'status': None,
                'message': 'Error connecting to PassaporteWeb',
            }

        except requests.exceptions.Timeout as e:
            error_dict = {
                '__all__': [error_messages.get('Timeout', error_messages['default']), ]
            }
            error = {
                'status': None,
                'message': 'Timeout connecting to PassaporteWeb',
            }

        except (requests.exceptions.RequestException, Exception) as e:
            error_dict = {
                '__all__': [error_messages.get('default'), ]
            }
            error = {
                'status': None,
                'message': u'Unexpected error: {0} <{1}>'.format(e, type(e)),
            }

        if error_dict:
            form._errors = prepare_form_errors(error_dict)

        if error:
            logging.error(
                'update_user_api: Error making request: %s - %s',
                error['status'], error['message']
            )

        return (status_code, content, form)


    @classmethod
    def fetch_association_data(cls, api_path):

        status_code = 500
        content = error = None

        if api_path.startswith(cls.api_host):
            url = api_path
        else:
            url = "{0}{1}".format(cls.api_host, api_path)

        try:
            logging.info('fetch_association_data: Making request to %s', url)
            response = cls.pweb.get(url)
            status_code = response.status_code

            if response.status_code == 200:
                content = response.json()

            else:
                response.raise_for_status()
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
                'fetch_association_data: Error making request: %s - %s',
                error['status'], error['message']
            )

        return status_code, content, error


    @classmethod
    def update_association_data(cls, new_data, api_path):

        status_code = 500
        content = error = None

        if api_path.startswith(cls.api_host):
            url = api_path
        else:
            url = "{0}{1}".format(cls.api_host, api_path)

        try:
            logging.info('update_association_data: Making request to %s', url)
            association_data = json.dumps(new_data)
            response = cls.pweb.put(url, headers={'content-length': str(len(association_data))}, data=association_data)
            status_code = response.status_code

            if response.status_code == 200:
                content = response.json()

            else:
                response.raise_for_status()
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
                'update_association_data: Error making request: %s - %s',
                error['status'], error['message']
            )

        return status_code, content, error


    @classmethod
    def fetch_user_accounts(cls, uuid, include_expired_accounts=False):

        status_code = 500
        content = error = None

        url = '{0}/organizations/api/identities/{1}/accounts/'.format(cls.api_host, uuid)

        try:
            logging.info('fetch_user_accounts: Making request to %s', url)
            response = cls.pweb.get(url, params={
                'include_expired_accounts': include_expired_accounts,
            })
            status_code = response.status_code

            if response.status_code == 200:
                content = response.json()

            else:
                response.raise_for_status()
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

        return status_code, content, error


    @classmethod
    def create_user_account(cls, uuid, name, plan_slug, expiration=None):

        status_code = 500
        content = error = None

        url = '{0}/organizations/api/identities/{1}/accounts/'.format(cls.api_host, uuid)

        try:
            logging.info('create_user_account: Making request to %s', url)

            account_data = {'name': name, 'plan_slug': plan_slug, 'expiration': expiration}
            account_data = json.dumps(account_data)

            response = cls.pweb.post(url, headers={'content-length': str(len(account_data))}, data=account_data)
            status_code = response.status_code

            if response.status_code in (200, 201):
                content = response.json()

            else:
                response.raise_for_status()
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
                'create_user_account: Error making request: %s - %s',
                error['status'], error['message']
            )

        return status_code, content, error


error_messages = {
    401: u"Esta aplicação não está autorizada a utilizar o PassaporteWeb. Entre em contato com o suporte.",
    400: u"Erro na transmissão dos dados. Tente novamente.",
    409: u"Email já cadastrado.",
    'ConnectionError': u"Ocorreu uma falha na comunicação com o Passaporte Web. Por favor tente novamente.",
    'Timeout': u"Ocorreu uma falha na comunicação com o Passaporte Web. Por favor tente novamente.",
    'default': u"Erro no servidor. Entre em contato com o suporte.",
}
