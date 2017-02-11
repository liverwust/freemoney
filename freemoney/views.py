from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_safe


@require_safe
def index(request):
    return redirect(reverse('fm_apply:welcome'), permanent=True)
