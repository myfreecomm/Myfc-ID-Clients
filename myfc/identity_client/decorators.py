# coding: UTF-8
from django import http

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
