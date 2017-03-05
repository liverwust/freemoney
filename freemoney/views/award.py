from collections import namedtuple
from django import forms
from django.shortcuts import render
from freemoney.models import ScholarshipAward
from freemoney.models.award import get_semester_awards
from freemoney.validation import CustomValidationIssueSet
import re


from .common import WizardPageView


class AwardPage(WizardPageView):
    """Page where the scholarship awards are selected."""

    page_name = 'award'

    def hook_save_changes(self):
        selection_re = re.compile(r'^selection_(\d+)$')
        chosen_awards = set()
        for key, value in self.request.POST.items():
            match = selection_re.match(key)
            if match != None and value != "":
                award_id = int(match.group(1))
                award = ScholarshipAward.objects.get(pk=award_id)
                chosen_awards.add(award)
            self.application.scholarshipaward_set.set(chosen_awards)
            self.application.full_clean()
            self.application.save()
        return True

    def hook_check_can_proceed(self):
        issues = CustomValidationIssueSet()

    def render_page(self, context):
        all_awards = ScholarshipAward.objects.all()
        selected_awards = self.application.scholarshipaward_set.all()
        selections = []
        for award in all_awards:
            selection = ScholarshipAwardSelection(
                    pk='selection_{}'.format(award.pk),
                    selected=(award in selected_awards),
                    name=award.name,
                    description=award.description
            )
            selections.append(selection)
        context['selections'] = selections
        return render(self.request, 'awards.html', context=context)

        picker = self.application.scholarshipawardpicker
        awards = picker.scholarshipaward_set.order_by('position')
        context['formset'] = ScholarshipAwardFormset(queryset=awards)
        return render(self.request, 'award.html', context=context)

    def save_changes(self):



ScholarshipAwardSelection = namedtuple('ScholarshipAwardSelection', [
        'pk', 'name', 'description', 'selected'
])
