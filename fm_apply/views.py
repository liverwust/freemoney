import abc
from collections import namedtuple
from django import forms
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_safe, require_http_methods
from fm_apply.models import ApplicantResponse, ScholarshipAwardPrompt
import logging


class BaseWizardView(abc.ABC):
    """Base class providing generic services to wizard views."""

    def __call__(self, request, *args, **kwargs):
        self.request = request
        self.index = None
        self.step = None
        self.application = None
        self.buttons = []
        for index, step in enumerate(STEPS):
            if isinstance(self, step.view_class):
                self.index = index
                self.step = step
                break
        if 'app_id' in request.session:
            self.application = ApplicantResponse.objects.get(
                    pk=request.session['app_id']
            )
        if request.method == 'GET' or request.method == 'HEAD':
            self.context = {'STEPS': STEPS,
                            'postback': request.path,
                            'current_index': self.index,
                            'current_step': self.step,
                            'application': self.application}
            self.handle_get()
            self.context['buttons'] = self.buttons
            return render(request,
                          '{}.html'.format(self.step.short_identifier),
                          context=self.context)
        elif request.method == 'POST':
            postdata = dict(request.POST)
            logging.getLogger('django').info(str(postdata))
            if 'submit-type' in postdata:
                new_index = None
                if postdata['submit-type'][0] == 'Start':
                    if self.index == 0:
                        new_index = 1
                elif postdata['submit-type'][0] == 'Cancel':
                    new_index = 0
                elif postdata['submit-type'][0] == 'Previous':
                    if self.index > 1:
                        new_index = self.index - 1
                elif postdata['submit-type'][0] == 'Next':
                    if (self.index + 1) < len(STEPS):
                        new_index = self.index + 1
                elif postdata['submit-type'][0] == 'Submit':
                    if (self.index + 1) == len(STEPS):
                        del(request.session['app_id'])
                        return HttpResponse('success!')
                del(postdata['submit-type'])
            self.handle_post(postdata)
            # TODO: get reverse routing lookup working
            if new_index == None:
                return redirect('/steps/'+self.step.short_identifier)
            else:
                return redirect('/steps/' + STEPS[new_index].short_identifier)
            return redirect(next_view)
        else:
            raise ValueError('bad HTTP method')

    @abc.abstractmethod
    def handle_get(self):
        pass

    @abc.abstractmethod
    def handle_post(self, postdata):
        pass


class WelcomeWizardView(BaseWizardView):
    def handle_get(self):
        self.buttons = ['Start']

    def handle_post(self, postdata):
        pass


class AwardSelectionWizardView(BaseWizardView):
    class AwardSelectionForm(forms.Form):
        award_selections = forms.ModelMultipleChoiceField(
                queryset=ScholarshipAwardPrompt.objects.all()
        )

    def handle_get(self):
        form = AwardSelectionWizardView.AwardSelectionForm()
        form.award_selections = self.application.scholarshipaward_set
        self.context['form'] = form

    def handle_post(self, postdata):
        form = AwardSelectionWizardView.AwardSelectionForm(postdata)
        self.application.scholarshipaward_set = form.award_selections


StepDescription = namedtuple('StepDescription', [
        'short_identifier',
        'full_name',
        'view_class',
])
STEPS = [StepDescription(short_identifier='welcome',
                         full_name='Welcome',
                         view_class=WelcomeWizardView),
         StepDescription(short_identifier='awards',
                         full_name='Award Selection',
                         view_class=AwardSelectionWizardView)]


@require_safe
def index(request):
    return redirect(STEPS[0].view_class(), permanent=True)
