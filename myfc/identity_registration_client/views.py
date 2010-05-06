# -*- coding: utf-8 -*_
import json
import httplib2

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.conf import settings
from django.http import HttpResponse

from identity_registration_client.forms import RegistrationForm

def new_identity(request):
    context = RequestContext(request, {'form': RegistrationForm(),})
    return render_to_response('registration_form.html', context)

def register_identity(request):
    form = RegistrationForm(request.POST)
    registration_data = json.dumps(form.data)

    api_user = settings.REGISTRATION_API['USER']
    api_password = settings.REGISTRATION_API['PASSWORD']
    api_url = "%s/%s" % (
        settings.REGISTRATION_API['HOST'],
        settings.REGISTRATION_API['PATH']
    )

    http = httplib2.Http()
    http.add_credentials(api_user, api_password)
    response, content = http.request(api_url,
                                "POST", body=registration_data,
                                headers={'content-type':'application/json'})

    if response.status == 409:
        try:
            content = json.loads(content)
            form._errors = content
        except ValueError:
            form._errors = {'__all__':
                        [u"Ops! Erro na transmissão dos dados. Tente de novo."]}

        context = RequestContext(request, {'form': form,})

        return render_to_response('registration_form.html', context)

    return HttpResponse(content)
