# -*- coding: utf-8 -*-
import json
import httplib2

from django.conf import settings

class APIClient(object):

    @classmethod
    def fetch_user_accounts(cls, uuid):
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
