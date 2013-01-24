#coding: utf-8
import oauth2 as oauth

from django.conf import settings
from django.core.urlresolvers import reverse, set_script_prefix

class SSOClient(oauth.Client):

    request_token_url = '%(HOST)s/%(REQUEST_TOKEN_PATH)s' % settings.MYFC_ID
    access_token_url = '%(HOST)s/%(ACCESS_TOKEN_PATH)s' % settings.MYFC_ID
    authorization_url = '%(HOST)s/%(AUTHORIZATION_PATH)s' % settings.MYFC_ID
    user_data_url = '%(HOST)s/%(FETCH_USER_DATA_PATH)s' % settings.MYFC_ID

    def __init__(self, *args, **kwargs):

        self.consumer = oauth.Consumer(
            settings.MYFC_ID['CONSUMER_TOKEN'],
            settings.MYFC_ID['CONSUMER_SECRET']
        )

        return super(SSOClient, self).__init__(self.consumer, *args, **kwargs)


    def fetch_request_token(self, callback_url=None):
        set_script_prefix(settings.APPLICATION_HOST)

        if callback_url is None:
            callback_url = reverse('sso_consumer:callback')

        resp, content = self.post(
            self.request_token_url, body='oauth_callback={0}'.format(callback_url)
        )

        if not str(resp.get('status')) == '200':
            raise AssertionError(resp, content)

        return oauth.Token.from_string(content)


    def fetch_access_token(self):

        resp, content = self.post(self.access_token_url)

        if not str(resp.get('status')) == '200':
            raise AssertionError(resp, content)

        return oauth.Token.from_string(content)


    def authorize(self, request):
        request_token = self.fetch_request_token()

        request.session['request_token'] = {request_token.key: request_token.secret}
        request.session['next_url'] = request.GET.get('next', settings.LOGIN_REDIRECT_URL)
        request.session.save()

        return '{0}?oauth_token={1}'.format(
            self.authorization_url, request_token.key
        )


    def get(self, url, **kwargs):
        resp, content = self.request(url, method='GET', **kwargs)
        
        return resp, content


    def post(self, url, **kwargs):
        resp, content = self.request(url, method='POST', **kwargs)
        
        return resp, content
