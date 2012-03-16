#coding: utf-8
try:
    import json
except ImportError:
    import simplejson as json

import httplib2

from django.conf import settings

from identity_client.utils import prepare_form_errors


__all__ = ['APIClient']


class APIClient(object):

    api_host = settings.MYFC_ID['HOST']
    api_user = settings.MYFC_ID['CONSUMER_TOKEN']
    api_password = settings.MYFC_ID['CONSUMER_SECRET']
    profile_api = settings.MYFC_ID['PROFILE_API']
    registration_api = settings.MYFC_ID['REGISTRATION_API']


    @classmethod
    def fetch_user_accounts(cls, uuid):
        api_user = cls.api_user
        api_password = cls.api_password

        http = httplib2.Http()
        url = '%s/%s' % (
            cls.api_host,
            'organizations/api/identities/{0}/accounts/'.format(uuid)
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

        # Efetuar requisição
        http = httplib2.Http()
        http.add_credentials(api_user, api_password)

        response, content = http.request(api_uri)
        return (response.status, content)


    @classmethod
    def invoke_registration_api(cls, form):
        registration_data = json.dumps(form.data)

        api_user = cls.api_user
        api_password = cls.api_password
        api_url = "%s/%s" % (
            cls.api_host,
            cls.registration_api
        )

        http = httplib2.Http()
        http.add_credentials(api_user, api_password)

        status_code = 500
        content = None
        error_dict = None

        try:
            response, content = http.request(api_url,
                "POST", body=registration_data,
                headers={
                    'content-type': 'application/json',
                    'user-agent': 'myfc_id client',
                    'cache-control': 'no-cache'
                }
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
    def fetch_association_data(cls, api_path):

        # Construir url da API
        api_user = cls.api_user
        api_password = sels.api_password
        api_host = cls.api_host

        api_uri = "%s%s" % (api_host, api_path)

        # Efetuar requisição
        http = httplib2.Http()
        http.add_credentials(api_user, api_password)

        response, content = http.request(
            api_uri,
            headers={
                'content-type': 'application/json',
                'user-agent': 'myfc_id client',
                'cache-control': 'no-cache'
            }
        )
        return (response.status, content)


    @classmethod
    def update_user_api(cls, form, api_path):
        registration_data = json.dumps(form.data)

        api_user = cls.api_user
        api_password = cls.api_password
        api_host = cls.api_host

        if api_path.startswith(api_host):
            api_url = api_path
        else:
            api_url = "%s%s" % (api_host, api_path)

        http = httplib2.Http()
        http.add_credentials(api_user, api_password)
        response, content = http.request(
            api_url,
            "PUT", body=registration_data,
            headers={'content-type':'application/json'}
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
