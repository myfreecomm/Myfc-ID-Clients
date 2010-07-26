#coding: utf-8
import oauth2 as oauth
import httplib2

from django.conf import settings

class SSOClient(oauth.Client):

    def __init__(self):
        self.request_token_url = '%(HOST)s/%(REQUEST_TOKEN_PATH)s' % settings.SSO
        self.access_token_url = '%(HOST)s/%(ACCESS_TOKEN_PATH)s' % settings.SSO
        self.user_data_url = '%(HOST)s/%(FETCH_USER_DATA_PATH)s' % settings.SSO

    def create_token(self, string):
        """
        Creates an request/access token from a given string
        """
        try:
            token = oauth.Token.from_string(string)
        except ValueError:
            token = None

        return token

    def call_oauth_provider(self, url, oauth_request):
        headers = oauth_request.to_header()
        #XXX: Por algum motivo o ouath2 tira o scope dos headers
        headers['Authorization'] = '%s, scope="%s"' %(headers['Authorization'], oauth_request['scope'])

        try:
            http = httplib2.Http()
            response, content = http.request(url,
                                             method="POST",
                                             headers=headers)
        except AttributeError:
            raise httplib2.HttpLib2Error

        return response, content

    def fetch_request_token(self, oauth_request):
        response, content = self.call_oauth_provider(self.request_token_url,
                                                     oauth_request)

        return self.create_token(content)

    def fetch_access_token(self, oauth_request):
        response, content = self.call_oauth_provider(self.access_token_url,
                                                     oauth_request)

        return self.create_token(content)

    def access_user_data(self, oauth_request):
        headers = {'Content-Type' :'application/x-www-form-urlencoded'}
        con = httplib2.Http()
        response, content = con.request(self.user_data_url, method='POST',
                                    body=oauth_request.to_postdata(), headers=headers)
        return content
