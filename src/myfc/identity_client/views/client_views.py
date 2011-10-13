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
from identity_client.utils import prepare_form_errors

__all__ = ["new_identity", "register", "login", "show_login"]

@required_method("GET")
def new_identity(request,template_name='registration_form.html',
          redirect_field_name=REDIRECT_FIELD_NAME,
          registration_form=RegistrationForm, **kwargs):

    if request.user.is_authenticated():
        return redirect_logged_user(request, redirect_field_name)

    form = registration_form()
    return handle_redirect_to(
        request, template_name, redirect_field_name, form, **kwargs
    )


@required_method("POST")
def register(request, template_name='registration_form.html',
          redirect_field_name=REDIRECT_FIELD_NAME,
          registration_form=RegistrationForm, **kwargs):

    form = registration_form(data=request.POST)
    if form.is_valid():
        # Registro
        status, content, form = invoke_registration_api(form)
        if status == 200:
            content = json.loads(content)
            user = MyfcidAPIBackend().create_local_identity(content)
            login_user(request, user)
            return redirect_logged_user(request, redirect_field_name)

    return handle_redirect_to(
        request, template_name, redirect_field_name, form, **kwargs
    )


@required_method("GET")
def show_login(request, template_name='login.html',
          redirect_field_name=REDIRECT_FIELD_NAME,
          authentication_form=AuthenticationForm, **kwargs):

    if request.user.is_authenticated():
        return redirect_logged_user(request, redirect_field_name)

    form = authentication_form()
    return handle_redirect_to(
        request, template_name, redirect_field_name, form, **kwargs
    )


@required_method("POST")
def login(request, template_name='login.html',
          redirect_field_name=REDIRECT_FIELD_NAME,
          authentication_form=AuthenticationForm, **kwargs):

    form = authentication_form(data=request.POST)
    if form.is_valid():
        user = form.get_user()
        login_user(request, user)
        result = redirect_logged_user(request, redirect_field_name)
    else:
        result = handle_redirect_to(
            request, template_name, redirect_field_name, form, **kwargs
        )

    return result


#======================================


def login_user(request, user):
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


def redirect_logged_user(request, redirect_field_name):
    # Redirecionar usuário para a pagina desejada
    redirect_to = request.REQUEST.get(redirect_field_name, '')
    if not redirect_to or '//' in redirect_to or ' ' in redirect_to:
        redirect_to = settings.LOGIN_REDIRECT_URL

    return HttpResponseRedirect(redirect_to)


def handle_redirect_to(request, template_name, redirect_field_name, form, **kwargs):

    context = kwargs.get('extra_context', {})

    redirect_to = request.REQUEST.get(redirect_field_name, '')

    request.session.set_test_cookie()

    if Site._meta.installed:
        current_site = Site.objects.get_current()
    else:
        current_site = RequestSite(request)

    context.update({
        'form': form,
        redirect_field_name: redirect_to,
        'site': current_site,
        'site_name': current_site.name,
    })
    return render_to_response(
        template_name,
        context,
        context_instance=RequestContext(request)
    )


def invoke_registration_api(form):
    registration_data = json.dumps(form.data)

    api_user = settings.MYFC_ID['CONSUMER_TOKEN']
    api_password = settings.MYFC_ID['CONSUMER_SECRET']
    api_url = "%s/%s" % (
        settings.MYFC_ID['HOST'],
        settings.MYFC_ID['REGISTRATION_API'],
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

    if response.status in (400, 409):
        try:
            error_dict = json.loads(content)
        except ValueError:
            error_dict = {
                '__all__': [u"Erro na transmissão dos dados. Aguarde alguns instantes e tente novamente."]
            }

        form._errors = prepare_form_errors(error_dict)
    elif response.status in (401, 403):
        error_dict = {
            '__all__': [u"Erro na configuração do projeto. Credenciais incorretas ou acesso negado."]
        }

        form._errors = prepare_form_errors(error_dict)

    return (response.status, content, form)
