from datetime import datetime, timezone
from django import forms
from django.contrib import auth
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_safe
from django.views.defaults import server_error
from freemoney.models import Application
import functools


def generate_nav_links(current_step):
    """Logic for generating nav "pill" links around the current step.
    
    See application.html for the context where this data is ultimately used.
    """

    base_context = {'steps': []}
    for short_name, long_name in [('welcome', 'Welcome'),
                                  ('awards', 'Choose Awards')]:
                                  #('feedback', 'Peer Feedback')]:
        uri = reverse('freemoney:' + short_name)
        is_active = (short_name == current_step)
        is_enabled = True  # TODO: hacked
        base_context['steps'].append((long_name, uri, is_active, is_enabled))
    return base_context


def fields_required_beyond_step(previous_step, fields):
    """Declare fields which must be completed prior to this wizard step.

    If any of the provided fields return validation errors, automatically
    redirect back to the previous step. This might happen recursively. The
    idea is to prevent jumping forward prematurely (despite the model layer's
    partial ability to handle nonlinear flow) in order to simplify testing.

    This decorator is a no-op if the current user doesn't yet have a partial
    (or complete) application. This condition can and should be checked by
    individual view functions.
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view_func(request):
            if 'application' in request.session:
                application= Application.objects.get(
                        pk=request.session['application']
                )
                try:
                    if application.submitted:
                        # TODO: handle (much) more gracefully
                        return server_error()
                    else:
                        application.full_clean(force=True)
                except ValidationError as exc:
                    for field in fields:
                        if field in exc.error_dict:
                            return redirect(reverse(previous_step) +
                                            '?with=errors')
            return view_func(request)
        return wrapped_view_func
    return decorator
