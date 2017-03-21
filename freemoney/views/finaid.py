from collections import namedtuple
from django.core.exceptions import ValidationError
from django.forms import (BaseFormSet,
                          BooleanField,
                          CharField,
                          ChoiceField,
                          Form,
                          formset_factory,
                          HiddenInput,
                          IntegerField)
from django.template import RequestContext, Template
from django.utils.safestring import mark_safe
from freemoney.models import (FinancialAid,
                              Semester)

from .common import WizardPageView
from .basicinfo import BasicInfoPage


# "Other" is automatically added later
AID_TYPES = [('government_loan', 'Federal or State loan'),
             ('private_loan', 'Private loan'),
             ('government_grant', 'Federal or State grant'),
             ('private_grant', 'Private grant'),
             ('triangle_scholarship', 'Triangle scholarship'),
             ('psu_scholarship', 'Penn State scholarship'),
             ('other_scholarship', 'Other scholarship'),
             ('work_study', 'Work Study program'),
             ('income', 'Personal or family income')]


class FinancialAidPage(WizardPageView):
    """Page on which sources and amounts of financial aid are recorded."""

    page_name = 'finaid'
    prev_page = BasicInfoPage

    _direct_copy = ['aid_type',
                    'provider',
                    'installment_frequency']

    @staticmethod
    def progress_sentry(issues):
        if len(issues.search(section='finaid')) > 0:
            return False
        else:
            return True

    def prepopulate_form(self):
        self._form_errors = []
        initial_data = []
        for finaid in self.application.financialaid_set.iterator():
            initial_data_row = {'finaid_id': finaid.pk}

            for copy_field in FinancialAidPage._direct_copy:
                initial_data_row[copy_field] = getattr(finaid, copy_field)

            if finaid.semester_finished is None:
                when_finished = ('', None)
            else:
                when_finished = finaid.semester_finished.semester_tuple

            initial_data_row['semestertype_finished'] = when_finished[0]
            initial_data_row['year_finished'] = when_finished[1]

            if finaid.installment_amount is None:
                initial_data_row['installment_amount'] = ''
            else:
                amount = '{:0.2f}'.format(finaid.installment_amount)
                initial_data_row['installment_amount'] = amount

            self._form_errors.append((finaid.pk, []))
            initial_data.append(initial_data_row)

        return FinancialAidFormSet(initial=initial_data)

    def parse_form(self):
        return FinancialAidFormSet(self.request.POST)

    def save_changes(self):
        submit_type = self.request.POST.get('submit-type')
        if submit_type.startswith('delete-'):
            delete_pk = int(submit_type.replace('delete-', ''))
            FinancialAid.objects.get(
                    application=self.application,
                    pk=delete_pk
            ).delete()
        else:
            delete_pk = None

        current_finaids = set(self.application.financialaid_set.iterator())
        preserved_finaids = set()
        for individual in self.form:
            if individual.empty_permitted:
                if individual.is_entirely_blank:
                    continue
                else:
                    finaid = FinancialAid.objects.create(
                            application=self.application
                    )
                    current_finaids.add(finaid)
                    preserved_finaids.add(finaid)
            elif individual.cleaned_data['finaid_id'] == delete_pk:
                continue
            else:
                finaid = None
                for finaid_try in current_finaids:
                    if finaid_try.pk == individual.cleaned_data['finaid_id']:
                        finaid = finaid_try
                        preserved_finaids.add(finaid)
                        break
                if finaid is None:
                    raise KeyError('invalid primary key provided')

            for field in FinancialAidPage._direct_copy:
                if field in individual.cleaned_data:
                    setattr(finaid, field, individual.cleaned_data[field])

            try:
                finaid.installment_amount = float(
                        individual.cleaned_data['installment_amount']
                )
            except KeyError:
                finaid.installment_amount = None
            except ValueError:
                finaid.installment_amount = None

            when_finished = (individual.cleaned_data['semestertype_finished'],
                             individual.cleaned_data['year_finished'])
            if when_finished[0] != '' and when_finished[1] is not None:
                finaid.semester_finished = Semester(when_finished)

            finaid.full_clean()
            finaid.save()

        for removed_finaid in current_finaids - preserved_finaids:
            removed_finaid.delete()

    def add_issues_to_form(self):
        row_errors = {('aid_type', 'required'): 'Aid type is required',
                      ('provider', 'required'): 'Provider is required',
                      ('installment_frequency', 'required'): 'Frequency is required',
                      ('installment_amount', 'required'): 'Amount is required',
                      ('installment_amount', 'invalid'): 'Amount is invalid, too small, or too large',
                      ('semester_finished', 'invalid'): 'Reported semester is in the past'}

        for issue in self.issues.search(section='finaid', discard=True):
            form_errors = None
            for candidate in self._form_errors:
                primary_key, candidate_errors = candidate
                if primary_key == issue.subfield:
                    form_errors = candidate_errors
                    break

            if issue.field == 'semester_finished':
                form_errors.append((
                        'semestertype_finished',
                        row_errors[(issue.field, issue.code)]
                ))
            else:
                form_errors.append((
                        issue.field,
                        row_errors[(issue.field, issue.code)]
                ))

    @staticmethod
    def _switch_even_odd(x):
        if x == 'odd':
            return 'even'
        else:
            return 'odd'

    def finalize_context(self):
        self.context['the_table'] = '<table></table>'

        label_row = ''
        help_text_row = ''
        even_odd = 'odd'
        for label_set in [('Type of aid', 2,
                           'Select the nearest choice, or Other'),
                          ('Provider', 3,
                           'Full name of the organization, sponsor, etc.'),
                          ('End date', 2,
                           'The last semester during which you will be receiving these funds (leave blank if not applicable)'),
                          ('Installment amount', 2,
                           'How much do you receive with each installment?'),
                          ('Installment frequency', 2,
                           'How often do you receive this money?')]:
            label_row += '<th class="{}" colspan="{}">{}</th>'.format(
                    even_odd,
                    label_set[1],
                    label_set[0]
            )
            help_text_row += '<td class="{}" colspan="{}">{}</td>'.format(
                    even_odd,
                    label_set[1],
                    label_set[2]
            )
            even_odd = FinancialAidPage._switch_even_odd(even_odd)

        if self.form.total_form_count() > 1:
            label_row += '<th class="{}" colspan="1">&nbsp;</th>'.format(
                    even_odd
            )
            help_text_row += '<th class="{}" colspan="1">&nbsp;</th>'.format(
                    even_odd
            )
            even_odd = FinancialAidPage._switch_even_odd(even_odd)

        insert_at = self.context['the_table'].find('</table>')
        self.context['the_table'] = (self.context['the_table'][0:insert_at] +
                                     '<tr>{}</tr>'.format(label_row) +
                                     '<tr>{}</tr>'.format(help_text_row) +
                                     self.context['the_table'][insert_at:])

        for row_index, individual in enumerate(self.form):
            template = Template('{% load bootstrap3 %}{% ' + " ".join([
                                        'bootstrap_field',
                                        'field',
                                        'show_label=False']) +
                                ' %}')
            subcontext = RequestContext(self.request)
            subcontext.update({'field': individual['finaid_id']})
            self.context['the_table'] += template.render(subcontext)

            body_row = ''
            even_odd = 'odd'

            errors_by_field = {}
            if not individual.empty_permitted:
                if len(self._form_errors[row_index][1]) > 0:
                    for form_error in self._form_errors[row_index][1]:
                        field, error = form_error
                        if field in errors_by_field:
                            errors_by_field[field].append(error)
                        else:
                            errors_by_field[field] = [error]

            for field_set in [('aid_type', 2, None, None),
                              ('provider', 3, None, None),
                              ('semestertype_finished', 1, None, 'left-combine'),
                              ('year_finished', 1, None, 'right-combine'),
                              ('installment_amount', 2, '$', None),
                              ('installment_frequency', 2, None, None)]:
                if field_set[2] is None:
                    template = Template('{% load bootstrap3 %}{% ' + " ".join([
                                                'bootstrap_field',
                                                'field',
                                                'show_label=False']) +
                                        ' %}')
                else:
                    template = Template('{% load bootstrap3 %}{% ' + " ".join([
                                                'bootstrap_field',
                                                'field',
                                                'addon_before="{}"'.format(field_set[2]),
                                                'show_label=False']) +
                                        ' %}')

                if field_set[3] is None:
                    classes = even_odd
                    even_odd = FinancialAidPage._switch_even_odd(even_odd)
                elif field_set[3] == 'left-combine':
                    classes = " ".join([even_odd, field_set[3]])
                    # don't switch yet
                elif field_set[3] == 'right-combine':
                    classes = " ".join([even_odd, field_set[3]])
                    even_odd = FinancialAidPage._switch_even_odd(even_odd)

                if field_set[0] in errors_by_field:
                    error_list = '<ul></ul>'
                    for error in errors_by_field[field_set[0]]:
                        insert_at = error_list.find('</ul>')
                        error_list = (error_list[0:insert_at] +
                                      '<li>{}</li>'.format(error) +
                                      error_list[insert_at:])
                else:
                    error_list = ''

                subcontext = RequestContext(self.request)
                subcontext.update({'field': individual[field_set[0]]})
                body_row = (body_row +
                            '<td class="{}" colspan="{}">{}{}</td>'.format(
                                    classes,
                                    field_set[1],
                                    template.render(subcontext),
                                    error_list))

            if self.form.total_form_count() > 1:
                body_row += '<td class="{}" colspan="1"></td>'.format(
                        even_odd
                )
                even_odd = FinancialAidPage._switch_even_odd(even_odd)

            insert_at = self.context['the_table'].rfind('<tr>')
            self.context['the_table'] = (self.context['the_table'][0:insert_at] +
                                        '<tr>{}</tr>'.format(body_row) +
                                        self.context['the_table'][insert_at:])

        self.context['the_table'] = mark_safe(self.context['the_table'])

class FinancialAidForm(Form):
    """Django form which represents a single FinancialAid record"""

    finaid_id = IntegerField(widget=HiddenInput, required=False)
    aid_type = ChoiceField(required=False,
                           choices=([('', '- Select -')] +
                                    AID_TYPES +
                                    [('other', 'Other')]))
    provider = CharField(required=False)
    year_finished = IntegerField(required=False)
    semestertype_finished = ChoiceField(
            required=False,
            choices=[('', '- Select -'),
                     ('Spring', 'Spring'),
                     ('Fall', 'Fall')]
    )
    installment_amount = CharField(required=False)
    installment_frequency = ChoiceField(required=False,
            choices = [('', '- Select -'),
                       ('yearly', 'per year'),
                       ('semesterly', 'per semester'),
                       ('monthly', 'per month')]
    )

    @property
    def is_entirely_blank(self):
        if (self.cleaned_data.get('aid_type', '') == '' and
            self.cleaned_data.get('provider', '') == '' and
            self.cleaned_data.get('semester_finished', None) is None and
            self.cleaned_data.get('installment_frequency', '') == '' and
            self.cleaned_data.get('installment_amount', '') == ''):
            return True
        else:
            return False


FinancialAidFormSet = formset_factory(FinancialAidForm, extra=1)
