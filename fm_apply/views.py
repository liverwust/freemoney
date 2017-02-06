from collections import namedtuple
from django.forms import Form, ModelForm
from django.shortcuts import render, redirect
from django.views.decorators.http import require_safe, require_http_methods
from fm_apply.models import ApplicantResponse


class _AwardSelectionForm(ModelForm):
    """Form used to select one or more awards to apply for."""

    class Meta:
        model = ApplicantResponse
        fields = []


class _PeerFeedbackForm(ModelForm):
    """Form used to provide (mandatory) feedback for several brothers."""

    class Meta:
        model = ApplicantResponse
        fields = []


class _BasicInformationForm(ModelForm):
    """Form used to provide basic contact and other information."""

    class Meta:
        model = ApplicantResponse
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
                         form_class=_AwardSelectionForm),
         StepDescription(short_identifier='feedback',
                         full_name='Peer Feedback',
                         form_class=_PeerFeedbackForm),
         StepDescription(short_identifier='basicinfo',
                         full_name='Basic Information',
                         form_class=_BasicInformationForm)]


@require_safe
def index(request):
    return redirect(static_wizard, 'welcome', permanent=True)


@require_http_methods(['GET', 'POST', 'HEAD'])
def static_wizard(request, current_step_identifier):
    context = {'STEPS': STEPS,
               'postback': request.path,
               'current_index': None,
               'current_step': None}
    for index, step in enumerate(STEPS):
        if step.short_identifier == current_step_identifier:
            context['current_index'] = index
            context['current_step'] = step
            break
    if (context['current_index'] == None or
        context['current_step'] == None):
        raise ValueError('invalid step identifier')

    if request.method == 'POST':
        new_index = context['current_index']
        if request.POST['submit-type'] == 'Start':
            if new_index == 0:
                new_index = 1
        elif request.POST['submit-type'] == 'Cancel':
            new_index = 0
        elif request.POST['submit-type'] == 'Previous':
            if new_index > 1:
                new_index -= 1
        elif request.POST['submit-type'] == 'Next':
            if (new_index + 1) < len(STEPS):
                new_index += 1
        elif request.POST['submit-type'] == 'Submit':
            if (new_index + 1) == len(STEPS):
                raise Exception('done-zo')
        return redirect(static_wizard, STEPS[new_index].short_identifier)

    else:
        if context['current_step'].short_identifier == 'welcome':
            return render(request,
                          template_name='welcome.html',
                          context=context)
        else:
            context['form'] = context['current_step'].form_class()
            return render(request,
                        template_name='form_postback.html',
                        context=context)
