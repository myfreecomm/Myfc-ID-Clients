#coding: utf-8
import logging
import oauth2 as oauth
import httplib2

from django.conf import settings
from django.core.urlresolvers import reverse, set_script_prefix

class SSOClient(oauth.Client):

    request_token_url = '%(HOST)s/%(REQUEST_TOKEN_PATH)s' % settings.MYFC_ID
    access_token_url = '%(HOST)s/%(ACCESS_TOKEN_PATH)s' % settings.MYFC_ID
    user_data_url = '%(HOST)s/%(FETCH_USER_DATA_PATH)s' % settings.MYFC_ID

    def __init__(self, *args, **kwargs):

        self.consumer = oauth.Consumer(
            settings.MYFC_ID['CONSUMER_TOKEN'],
            settings.MYFC_ID['CONSUMER_SECRET']
        )

        return super(SSOClient, self).__init__(self.consumer, *args, **kwargs)


    def fetch_request_token(self):
        set_script_prefix(settings.APPLICATION_HOST)
        self.callback_url = reverse('sso_consumer:callback')

        resp, content = self.request(
            self.request_token_url, method='POST', 
            body='oauth_callback={0}'.format(self.callback_url)
        )

        assert resp.get('status') == '200', (resp, content)
        return oauth.Token.from_string(content)


    def fetch_access_token(self):
        resp, content = self.request(
            self.access_token_url, method='POST', 
        )

        assert resp.get('status') == '200', (resp, content)
        return oauth.Token.from_string(content)


    def get(self, url):
        resp, content = self.request(url, method='GET')
        
        assert resp.get('status') == '200', (resp, content)
        return content


    def post(self, url):
        resp, content = self.request(url, method='POST')
        
        assert resp.get('status') == '200', (resp, content)
        return content
