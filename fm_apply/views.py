from collections import namedtuple
from django.forms import ModelForm
from django.shortcuts import render, redirect
from django.views.decorators.http import require_safe
from fm_apply.models import ApplicantResponse


class _AwardSelectionForm(ModelForm):
    """Form used to select one or more awards when applying."""

    class Meta:
        model = ApplicantResponse
        fields = ['scholarshipawards_set']
        fields = []


StepDescription = namedtuple('StepDescription', [
        'short_identifier',
        'full_name',
        'form_class',
])
STEPS = [StepDescription(short_identifier='welcome',
                         full_name='Welcome',
                         form_class=None),
         StepDescription(short_identifier='awards',
                         full_name='Award Selection',
                         form_class=_AwardSelectionForm)]


@require_safe
def index(request):
    return redirect(static_wizard, 'welcome', permanent=True)


def static_wizard(request, current_step_identifier):
    context = {'STEPS': STEPS, 'current_step': None}
    for step in STEPS:
        if step.short_identifier == current_step_identifier:
            context['current_step'] = step
            break
    if context['current_step'] == None:
        raise ValueError('invalid step identifier')
    elif context['current_step'].short_identifier == 'welcome':
        return render(request, template_name='welcome.html', context=context)
    else:
        context['form'] = context['current_step'].form_class()
        return render(request,
                      template_name='form_postback.html',
                      context=context)
