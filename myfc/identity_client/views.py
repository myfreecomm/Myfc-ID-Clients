# -*- coding: utf-8 -*-
import httplib2
import json

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.views.decorators.csrf import csrf_protect
from django.shortcuts import render_to_response
from django.contrib.sites.models import Site, RequestSite
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.views.decorators.cache import never_cache

from identity_client.backend import MyfcidAPIBackend
from identity_client.forms import RegistrationForm
from identity_client.decorators import required_method
from identity_client.forms import IdentityAuthenticationForm as AuthenticationForm

__all__ = ["new_identity", "register", "login", "show_login"]

@required_method("GET")
def new_identity(request,template_name='registration_form.html',
          redirect_field_name=REDIRECT_FIELD_NAME,
          registration_form=RegistrationForm):
    
    form = registration_form()
    return handle_redirect_to(request, template_name, redirect_field_name, form) 


@required_method("POST")
def register(request, template_name='registration_form.html',
          redirect_field_name=REDIRECT_FIELD_NAME,
          registration_form=RegistrationForm):

    form = registration_form(data=request.POST)
    if form.is_valid():
        # Registro
        status, content, form = invoke_registration_api(form)
        if status == 200:
            content = json.loads(content)
            user = MyfcidAPIBackend().create_local_identity(content)
            return login_user(request, user, redirect_field_name)
    
    return handle_redirect_to(request, template_name, redirect_field_name, form) 


@required_method("GET")
def show_login(request, template_name='login.html',
          redirect_field_name=REDIRECT_FIELD_NAME,
          authentication_form=AuthenticationForm):
   
    form = authentication_form()
    return handle_redirect_to(request, template_name, redirect_field_name, form) 


@required_method("POST")
def login(request, template_name='login.html',
          redirect_field_name=REDIRECT_FIELD_NAME,
          authentication_form=AuthenticationForm):
    
    form = authentication_form(data=request.POST)
    if form.is_valid():
        user = form.get_user()
        result = login_user(request, user, redirect_field_name)
    else:
        result = handle_redirect_to(request, template_name, redirect_field_name, form) 

    return result


#======================================


def login_user(request, user, redirect_field_name):
    # Efetuar login
    from django.contrib.auth import login as django_login
    django_login(request, user)
    # Adicionar dados adicionais do usuário à sessão
    try:
        request.session['user_data'] = user.user_data
        del(user.user_data)
    except AttributeError:
        request.session['user_data'] = {}

    if request.session.test_cookie_worked():
        request.session.delete_test_cookie()

    # Redirecionar usuário para a pagina desejada
    redirect_to = request.REQUEST.get(redirect_field_name, '')
    if not redirect_to or '//' in redirect_to or ' ' in redirect_to:
        redirect_to = settings.LOGIN_REDIRECT_URL

    return HttpResponseRedirect(redirect_to)


def handle_redirect_to(request, template_name, redirect_field_name, form):

    redirect_to = request.REQUEST.get(redirect_field_name, '')

    request.session.set_test_cookie()

    if Site._meta.installed:
        current_site = Site.objects.get_current()
    else:
        current_site = RequestSite(request)
 
    context = {
        'form': form,
        redirect_field_name: redirect_to,
        'site': current_site,
        'site_name': current_site.name,
    }
    return render_to_response(
        template_name,
        context,
        context_instance=RequestContext(request)
    )


def invoke_registration_api(form):
    registration_data = json.dumps(form.data)

    api_user = settings.REGISTRATION_API['USER']
    api_password = settings.REGISTRATION_API['PASSWORD']
    api_url = "%s/%s" % (
        settings.REGISTRATION_API['HOST'],
        settings.REGISTRATION_API['PATH'],
    )

    http = httplib2.Http()
    http.add_credentials(api_user, api_password)
    response, content = http.request(api_url,
        "POST", body=registration_data,
        headers={
            'content-type': 'application/json',
            'user-agent': 'myfc_id client',
            'cache-control': 'no-cache'
        }
    )

    if response.status == 409:
        try:
            content = json.loads(content)
            form._errors = content
        except ValueError:
            form._errors = {'__all__':
                        [u"Ops! Erro na transmissão dos dados. Tente de novo."]}

    return (response.status, content, form)
