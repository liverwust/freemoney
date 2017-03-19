from collections import namedtuple
from django.forms import (BooleanField,
                          CharField,
                          Form,
                          formset_factory,
                          HiddenInput,
                          IntegerField,
                          Textarea)
from django.shortcuts import render
from freemoney.models import (Award,
                              Semester)


from .common import WizardPageView
from .welcome import WelcomePage


class AwardPage(WizardPageView):
    """Page where the scholarship awards are selected."""

    page_name = 'award'
    prev_page = WelcomePage

    @staticmethod
    def progress_sentry(issues):
        if len(issues.search(section='award')) > 0:
            return False
        else:
            return True

    def prepopulate_form(self):
        initial_data = []
        selected_awards = self.application.award_set.all()
        due_semester = Semester(self.application.due_at)
        for award in Award.objects.for_semester(due_semester):
            new_data = {'award_id': award.pk,
                        'name': award.name,
                        'description': award.description}
            if award in selected_awards:
                new_data['selected'] = True
            else:
                new_data['selected'] = False
            initial_data.append(new_data)
        return AwardSelectionFormSet(initial=initial_data)

    def parse_form(self):
        return AwardSelectionFormSet(self.request.POST)

    def save_changes(self):
        chosen_awards = set()
        for single_form in self.form:
            award_id = single_form.cleaned_data['award_id']
            selected = single_form.cleaned_data['selected']
            if selected:
                award = Award.objects.get(pk=award_id)
                chosen_awards.add(award)
        self.application.award_set.set(chosen_awards)
        self.application.full_clean()
        self.application.save()

    def add_issues_to_form(self):
        if (len(self.issues.search(section='award',
                                   code='min-length',
                                   discard=True)) > 0):
            if self.form._non_form_errors == None:
                self.form._non_form_errors = []
            self.form._non_form_errors.append(
                    'Must choose at least one scholarship award'
            )
        for invalid_award in self.issues.search(section='award',
                                                field='[records]',
                                                code='invalid',
                                                discard=True):
            self.form[invalid_award.subfield].add_error(
                    None,
                    'Invalid or unknown award selection'
            )
        for issue in self.issues.search(section='award', discard=True):
            if self.form._non_form_errors == None:
                self.form._non_form_errors = []
            self.form._non_form_errors.append(str(issue))


class AwardSelectionForm(Form):
    """Selector for an individual scholarship award"""

    award_id = IntegerField(widget=HiddenInput)
    selected = BooleanField(required=False)
    name = CharField()
    description = CharField(widget=Textarea)


AwardSelectionFormSet = formset_factory(AwardSelectionForm, extra=0)
