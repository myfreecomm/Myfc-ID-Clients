#-*- coding: utf-8 -*-
from django import http
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import user_passes_test
from django.template import Context, loader

from requestlogging import logging
from identity_client.utils import get_account_module


__all__ = ['required_method', 'sso_login_required', 'requires_plan', 'with_403_page']


class required_method(object):

    def __init__(self, *args, **kwargs):
        self.methods = args
        self.error = kwargs.get('error',
            # Default error:
            http.HttpResponse('Not Implemented',
                mimetype='text/plain', status=501)
        )

    def __call__(self, view):
        def f(request, *args, **kwargs):
            if request.method in self.methods:
                return view(request, *args, **kwargs)
            else:
                return self.error
        f.__name__ = view.__name__
        f.__doc__ = view.__doc__
        return f


def sso_login_required(view):

    def decorated(request, *args, **kwargs):
        url = reverse('sso_consumer:request_token')

        actual_decorator = user_passes_test(
            lambda user: user.is_authenticated(),
            login_url=url,
        )

        wrapped_view = actual_decorator(view)

        return wrapped_view(request, *args, **kwargs)

    return decorated


def requires_plan(plan_slug):

    def decorator(view):

        @sso_login_required
        def check_user_plan(request, *args, **kwargs):
            """
            Este decorator assume que a autenticação acabou de ser feita, 
            portanto as contas do usuário estão sincronizadas com o Passaporte Web.
            """
            serviceAccount = get_account_module()
            user_accounts = serviceAccount.for_identity(request.user)
            required_plan_accounts = user_accounts.filter(plan_slug=plan_slug)

            if required_plan_accounts.count() > 0:
                return view(request, *args, **kwargs)
            else:
                logging.info(
                    'Request from user %s (uuid=%s) denied (%s). User has no accounts at plan "%s".',
                    request.user.email,
                    request.user.uuid,
                    request.path,
                    plan_slug,
                    request=request
                )
                return http.HttpResponseForbidden()

        return check_user_plan
        
    return decorator


def with_403_page(view):

    # You need to create a 403.html template.
    template_name = '403.html'

    def handle_403(request, *args, **kwargs):
        response = view(request, *args, **kwargs)

        if isinstance(response, http.HttpResponseForbidden):
            t = loader.get_template(template_name) 
            response = http.HttpResponseForbidden(
                t.render(
                    Context({'MEDIA_URL': settings.MEDIA_URL})
                )
            )

        return response

    return handle_403
