#-*- coding: utf-8 -*-
from django import http
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import user_passes_test

__all__ = ['required_method', 'sso_login_required', ]


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
