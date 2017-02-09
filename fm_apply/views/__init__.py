from django.shortcuts import redirect
from django.views.decorators.http import require_safe
from django.urls import reverse


from .welcome import wizard_welcome
from .awards import wizard_awards
#from .feedback import wizard_feedback


@require_safe
def index(request):
    return redirect(reverse('fm_apply:welcome'), permanent=True)
