from django import forms
from django.core.exceptions import ValidationError
from django.shortcuts import render
from freemoney.models import (ScholarshipAward)


from .common import WizardView


class AwardPage(WizardView):
    pass
#    """Page where the scholarship awards are selected."""
#
#    page_name = 'award'
#
#    def render_page(self, context):
#        picker = self.application.scholarshipawardpicker
#        awards = picker.scholarshipaward_set.order_by('position')
#        context['formset'] = ScholarshipAwardFormset(queryset=awards)
#        return render(self.request, 'award.html', context=context)
#
#    def save_changes(self):
#        picker = self.application.scholarshipawardpicker
#        awards = picker.scholarshipaward_set.order_by('position')
#        formset = ScholarshipAwardFormset(self.request.POST,
#                                          queryset=awards)
#        if formset.is_valid():
#            formset.save()
#            # proceed to next destination
#            return None
#        else:
#            # TODO: error handling
#            return server_error()
#
#
#class BaseScholarshipAwardFormset(forms.BaseModelFormSet):
#    def clean(self):
#        super(BaseScholarshipAwardFormset, self).clean()
#        application = None
#        for form in self.forms:
#            # Get a form's application w/o using a key or index
#            application = form.instance.application
#            break
#        application.scholarshipawardpicker.full_clean()
#
#
#ScholarshipAwardFormset = forms.modelformset_factory(
#        ScholarshipAward,
#        formset=BaseScholarshipAwardFormset,
#        fields = ['chosen', 'name', 'description'],
#        extra=0
#)
