from datetime import datetime, timezone
from django.contrib import auth
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from fm_apply import models as fm_models


from .common import generate_nav_links


@require_http_methods(['GET', 'HEAD', 'POST'])
def wizard_welcome(request):
    """Informational page at the beginning of the application wizard."""

    if 'full_response' in request.session:
        return redirect(reverse('fm_apply:awards'))
    else:
        if (request.method == 'POST' and
            request.POST.get('submit-type') == 'start'):
            new_full_response = fm_models.ApplicantResponse()
            # TODO: real applicant here
            #new_full_response.applicant = auth.models.User.objects.first()
            # TODO: real due date here
            new_full_response.due_at = datetime.now(timezone.utc)
            new_full_response.full_clean()
            new_full_response.save()
            request.session['full_response'] = new_full_response
            return redirect(reverse('fm_apply:awards'))
        else:
            context = generate_nav_links('welcome')
            context['buttons'] = ['start']
            return render('welcome.html', context=context)
