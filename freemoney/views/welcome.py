from datetime import datetime, timezone
from django.contrib import auth
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from freemoney.models import Application


from .common import generate_nav_links


@require_http_methods(['GET', 'HEAD', 'POST'])
def wizard_welcome(request):
    """Informational page at the beginning of the application wizard."""
    my_path = reverse('freemoney:welcome')

    if 'application' in request.session:
        return redirect(reverse('freemoney:awards'))
    else:
        if (request.method == 'POST' and
            request.POST.get('submit-type') == 'start'):
            new_application = Application.objects.create(
                    due_at=datetime.now(timezone.utc)
            )
            request.session['application'] = new_application.pk
            return redirect(reverse('freemoney:awards'))
        else:
            context = generate_nav_links('welcome')
            context['postback'] = my_path
            context['buttons'] = ['start']
            return render(request, 'welcome.html', context=context)
