# -*- coding: utf-8 -*_
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required

@login_required
def profile(request, template_name='registration/profile.html'):
    context = {
        'user': request.user,
        'user_data': request.session['user_data'],
    }
    return render_to_response(template_name, context)

