# -*- coding: utf-8 -*_
from django.shortcuts import render_to_response
from django.template import RequestContext

from identity_registration_client.forms import RegistrationForm

def new_identity(request):
    context = RequestContext(request, {'form': RegistrationForm(),})
    return render_to_response('registration_form.html', context)

def register_identity(request):
    pass
