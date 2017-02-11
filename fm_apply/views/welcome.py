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
    my_path = reverse('fm_apply:welcome')

    if 'full_response' in request.session:
        return redirect(reverse('fm_apply:awards'))
    else:
        if (request.method == 'POST' and
            request.POST.get('submit-type') == 'start'):
            new_full_response = fm_models.ApplicantResponse.objects.create(
                    due_at=datetime.now(timezone.utc)
            )
            request.session['full_response'] = new_full_response.pk
            return redirect(reverse('fm_apply:awards'))
        else:
            context = generate_nav_links('welcome')
            context['postback'] = my_path
            context['buttons'] = ['start']
            return render(request, 'welcome.html', context=context)
