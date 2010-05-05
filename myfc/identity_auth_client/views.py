# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.csrf import csrf_protect
from django.shortcuts import render_to_response
from django.contrib.sites.models import Site, RequestSite
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.views.decorators.cache import never_cache

@csrf_protect
@never_cache
def login(request, template_name='registration/login.html',
          redirect_field_name=REDIRECT_FIELD_NAME,
          authentication_form=AuthenticationForm):
    """
    Displays the login form and handles the login action.

    Shameless copy of the default django view, extracting
    additional user data from the authenticated user and adding
    it to the session.
    """
    redirect_to = request.REQUEST.get(redirect_field_name, '')
    if request.method == "POST":
        form = authentication_form(data=request.POST)
        if form.is_valid():
            # Light security check -- make sure redirect_to isn't garbage.
            if not redirect_to or '//' in redirect_to or ' ' in redirect_to:
                redirect_to = settings.LOGIN_REDIRECT_URL
            from django.contrib.auth import login
            user = form.get_user()
            login(request, user)

            # Insert additional user data in his session
            try:
                request.session['user_data'] = user.user_data
                del(user.user_data)
            except AttributeError:
                request.session['user_data'] = {}

            if request.session.test_cookie_worked():
                request.session.delete_test_cookie()
            return HttpResponseRedirect(redirect_to)
    else:
        form = authentication_form(request)
    request.session.set_test_cookie()
    if Site._meta.installed:
        current_site = Site.objects.get_current()
    else:
        current_site = RequestSite(request)
    return render_to_response(template_name, {
        'form': form,
        redirect_field_name: redirect_to,
        'site': current_site,
        'site_name': current_site.name,
    }, context_instance=RequestContext(request))

