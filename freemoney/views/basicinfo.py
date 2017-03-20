from django.core.exceptions import ValidationError
from django.forms import (BooleanField,
                          CharField,
                          ChoiceField,
                          Form,
                          IntegerField,
                          Textarea)
from freemoney.models import (Application,
                              Semester)
import re


from .common import WizardPageView
from .award import AwardPage


# "Other" is automatically added later
MAJORS = [
        'Aerospace Engineering',
        'Agricultural Science',
        'Agricultural and Extension Education',
        'Animal Science',
        'Archaeological Science',
        'Architectural Engineering',
        'Architecture',
        'Astronomy and Astrophysics',
        'BioRenewable Systems',
        'Biobehavioral Health',
        'Biochemistry and Molecular Biology',
        'Biological Anthropology',
        'Biological Engineering',
        'Biology',
        'Biomedical Engineering',
        'Biotechnology',
        'Chemical Engineering',
        'Chemistry',
        'Civil Engineering',
        'Computer Engineering',
        'Computer Science',
        'Earth Science and Policy',
        'Earth Sciences',
        'Electrical Engineering',
        'Electro-Mechanical Engineering Technology',
        'Energy Engineering',
        'Energy and Sustainability Policy',
        'Engineering Science',
        'Environmental Studies',
        'Environmental Systems Engineering',
        'Food Science',
        'Forensic Science',
        'General Engineering',
        'Geobiology',
        'Geography',
        'Geosciences',
        'Immunology and Infectious Disease',
        'Industrial Engineering',
        'Information Sciences and Technology',
        'Landscape Architecture',
        'Latin American Studies',
        'Management Information Systems',
        'Materials Science and Engineering',
        'Mathematics',
        'Mechanical Engineering',
        'Meteorology',
        'Microbiology',
        'Mining Engineering',
        'Nuclear Engineering',
        'Nutritional Sciences',
        'Petroleum and Natural Gas Engineering',
        'Physics',
        'Planetary Science and Astronomy',
        'Plant Sciences',
        'Premedicine',
        'Rail Transportation Engineering',
        'Risk Management',
        'Science',
        'Security and Risk Analysis',
        'Statistics',
        'Supply Chain and Information Systems',
        'Telecommunications',
        'Toxicology',
        'Turfgrass Science',
        'Wildlife and Fisheries Science',
]


class BasicInfoPage(WizardPageView):
    """Page where basic contact and demographic information is provided"""

    page_name = 'basicinfo'
    prev_page = AwardPage

    _direct_copy = ['address',
                    'phone',
                    'preferred_email',
                    'psu_id',
                    'major',
                    'emch_minor',
                    'in_state_tuition',
                    'additional_remarks']

    @staticmethod
    def progress_sentry(issues):
        if len(issues.search(section='basicinfo')) > 0:
            return False
        else:
            return True

    def prepopulate_form(self):
        initial_data = {}
        for field in BasicInfoPage._direct_copy:
            initial_data[field] = getattr(self.application, field)
        initial_data['psu_email'] = re.sub(r'@psu\.edu$',
                                           '',
                                           self.application.psu_email)

        if self.application.semester_gpa is None:
            initial_data['semester_gpa'] = ''
        else:
            initial_data['semester_gpa'] = '{:0.2f}'.format(
                    self.application.semester_gpa
            )

        if self.application.cumulative_gpa is None:
            initial_data['cumulative_gpa'] = ''
        else:
            initial_data['cumulative_gpa'] = '{:0.2f}'.format(
                    self.application.cumulative_gpa
            )

        if self.application.semester_initiated is None:
            when_initiated = ('', None)
        else:
            semester_initiated = self.application.semester_initiated
            when_initiated = semester_initiated.semester_tuple

        if self.application.semester_graduating is None:
            when_graduating = ('', None)
        else:
            semester_graduating = self.application.semester_graduating
            when_graduating = semester_graduating.semester_tuple

        initial_data['semestertype_initiated'] = when_initiated[0]
        initial_data['year_initiated'] = when_initiated[1]
        initial_data['semestertype_graduating'] = when_graduating[0]
        initial_data['year_graduating'] = when_graduating[1]
        return BasicInfoForm(initial_data)

    def parse_form(self):
        return BasicInfoForm(self.request.POST)

    def save_changes(self):
        for field in BasicInfoPage._direct_copy:
            setattr(self.application, field, self.form.cleaned_data[field])

        self.application.psu_email = re.sub(r'^([^@]+)$',
                                            r'\1@psu.edu',
                                            self.form.cleaned_data['psu_email'])

        if self.form.cleaned_data['semester_gpa'] == '':
            self.application.semester_gpa = None
        else:
            try:
                self.application.semester_gpa = float(
                        self.form.cleaned_data['semester_gpa']
                )
            except ValueError:
                self.application.semester_gpa = ''

        if self.form.cleaned_data['cumulative_gpa'] == '':
            self.application.cumulative_gpa = None
        else:
            try:
                self.application.cumulative_gpa = float(
                        self.form.cleaned_data['cumulative_gpa']
                )
            except ValueError:
                self.application.cumulative_gpa = ''

        when_initiated = (self.form.cleaned_data['semestertype_initiated'],
                          self.form.cleaned_data['year_initiated'])
        when_graduating = (self.form.cleaned_data['semestertype_graduating'],
                           self.form.cleaned_data['year_graduating'])
        if when_initiated[0] != '' and when_initiated[1] is not None:
            self.application.semester_initiated = Semester(when_initiated)
        if when_graduating[0] != '' and when_graduating[1] is not None:
            self.application.semester_graduating = Semester(when_graduating)

        self.application.full_clean()
        self.application.save()

    def add_issues_to_form(self):
        if (len(self.issues.search(section='basicinfo',
                                   field='psu_email',
                                   code='prohibited',
                                   discard=True)) > 0):
            self.form.add_error('psu_email',
                                'psu_email: Must be a psu.edu e-mail address')
        if (len(self.issues.search(section='basicinfo',
                                   field='semester_initiated',
                                   code='invalid',
                                   discard=True)) > 0):
            self.form.add_error(
                    'semestertype_initiated',
                    'semester_initiated: Semester is invalid, or is in the future'
            )
        if (len(self.issues.search(section='basicinfo',
                                   field='semester_graduating',
                                   code='invalid',
                                   discard=True)) > 0):
            self.form.add_error(
                    'semestertype_graduating',
                    'semester_graduating: Semester is invalid, or is in the past',
            )
        if (len(self.issues.search(section='basicinfo',
                                   field='semester_graduating',
                                   code='prohibited',
                                   discard=True)) > 0):
            self.form.add_error(
                    'semestertype_graduating',
                    'semester_graduating: Some of your award selections cannot be granted to graduating seniors (sorry!)'
            )
        if (len(self.issues.search(section='basicinfo',
                                   field='major',
                                   code='prohibited',
                                   discard=True)) > 0):
            self.form.add_error(
                    'major',
                    'major: Some of your award selections are incompatible with your major'
            )
        for remaining_issue in self.issues.search(section='basicinfo'):
            if remaining_issue.field == 'semester_initiated':
                the_field = 'semestertype_initiated'
                the_prefix = 'semester_initiated'
            elif remaining_issue.field == 'semester_graduating':
                the_field = 'semestertype_graduating'
                the_prefix = 'semester_graduating'
            else:
                the_field = remaining_issue.field
                the_prefix = the_field

            if remaining_issue.code == 'invalid':
                self.form.add_error(the_field, (the_prefix + ': ' +
                                    'Your current response is invalid'))
            elif remaining_issue.code == 'required':
                self.form.add_error(the_field, (the_prefix + ': ' +
                                    'This field must be filled in'))
            else:
                self.form.add_error(the_field, (the_prefix + ': ' +
                                    'Unknown error in this field'))


class BasicInfoForm(Form):
    """Enables providing basic contact and demographic information."""

    psu_id = CharField(label='PSU ID number',
                       help_text='Nine digits: 9xxxxxxxx',
                       required=False)
    psu_email = CharField(label='University e-mail address',
                          required=False)
    preferred_email = CharField(label='Preferred e-mail address',
                                help_text='Leave blank if same as above',
                                required=False)
    phone = CharField(label='Primary phone number',
                      help_text='Cell phone is acceptable',
                      required=False)
    address = CharField(label='Permanent mailing address',
                        help_text='Where can we mail your money (by check)?',
                        widget=Textarea,
                        required=False)
    major = ChoiceField(label='Major course of study',
                        help_text='Choose "Other" if your major is not listed',
                        required=False,
                        choices=([('', '- Please select -')] +
                                 list(zip(sorted(MAJORS) + ['Other'],
                                          sorted(MAJORS) + ['Other']))))
    emch_minor = BooleanField(
            label='Are you enrolled in the Engineering Mechanics minor?',
            required=False
    )
    year_initiated = IntegerField(label='Year of initiation',
                                  required=False)
    semestertype_initiated = ChoiceField(
            label='Semester of initiation',
            required=False,
            choices=[('', '- Please select -'),
                     ('Spring', 'Spring'),
                     ('Fall', 'Fall')]
    )
    year_graduating = IntegerField(label='(Projected) year of graduation',
                                   required=False)
    semestertype_graduating = ChoiceField(
            label='(Projected) semester of graduation',
            required=False,
            choices=[('', '- Please select -'),
                     ('Spring', 'Spring'),
                     ('Fall', 'Fall')]
    )
    semester_gpa = CharField(label='Semester GPA',
                             help_text='For the last completed semester',
                             required=False)
    cumulative_gpa = CharField(label='Cumulative GPA',
                               help_text='As of the end of last semester',
                               required=False)
    in_state_tuition = BooleanField(
            label='Do you live in Pennsylvania?',
            help_text='PA residents pay a reduced tuition rate at PSU',
            required=False
    )
    additional_remarks = CharField(
            label='Additional remarks',
            help_text='(optional) Anything you want us to know about you?',
            widget=Textarea,
            required=False
    )
