# -*- coding: utf-8 -*-
import httplib2
import json

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.csrf import csrf_protect
from django.shortcuts import render_to_response
from django.contrib.sites.models import Site, RequestSite
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.views.decorators.cache import never_cache

from identity_client.backend import MyfcidAPIBackend
from identity_client.forms import LoginOrRegisterForm, RegistrationForm

#__all__ = ['simple_login', 'register_identity', 'login_or_register']


def simple_login(request, template_name='login.html',
          redirect_field_name=REDIRECT_FIELD_NAME,
          authentication_form=AuthenticationForm):

    return login_or_register(
        request, template_name=template_name,
        redirect_field_name=redirect_field_name,
        action_form=authentication_form
    )

def register_identity(request, template_name='registration_form.html',
          redirect_field_name=REDIRECT_FIELD_NAME,
          registration_form=RegistrationForm):

    return login_or_register(
        request, template_name=template_name,
        redirect_field_name=redirect_field_name,
        action_form=registration_form
    )

@csrf_protect
@never_cache
def login_or_register(request, template_name='login_or_register.html',
          redirect_field_name=REDIRECT_FIELD_NAME,
          action_form=LoginOrRegisterForm, extra_context={}):

    context = extra_context

    redirect_to = request.REQUEST.get(redirect_field_name, '')

    if request.method == "POST":
        form = action_form(data=request.POST)
        if form.is_valid():
            # Light security check -- make sure redirect_to isn't garbage.
            if not redirect_to or '//' in redirect_to or ' ' in redirect_to:
                redirect_to = settings.LOGIN_REDIRECT_URL

            if ('password2' in form.cleaned_data) and \
             (form.cleaned_data['password'] == form.cleaned_data['password2']):
                # Registro
                status = 400

                try:
                    status, content, form = invoke_registration_api(form)
                    if status == 200:
                        content = json.loads(content)
                        user = MyfcidAPIBackend().create_local_identity(content)
                    else:
                        raise ValueError
                except ValueError:
                    context.update({
                        'form': form,
                        redirect_field_name: redirect_to,
                    })
                    return render_to_response(
                        template_name,
                        context,
                        context_instance=RequestContext(request)
                    )

            else:
                # login
                user = form.get_user()

            # Insert additional user data in his session
            from django.contrib.auth import login
            login(request, user)
            try:
                request.session['user_data'] = user.user_data
                del(user.user_data)
            except AttributeError:
                request.session['user_data'] = {}

            if request.session.test_cookie_worked():
                request.session.delete_test_cookie()
            return HttpResponseRedirect(redirect_to)

    else:
        form = action_form()

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
