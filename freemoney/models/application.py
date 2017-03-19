import datetime
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.conf import settings
from django.db.models import (Model,
                              CASCADE,
                              BooleanField,
                              DateTimeField,
                              FloatField,
                              ForeignKey,
                              TextField)
import freemoney.models
from freemoney.models import (CustomValidationIssue,
                              CustomValidationIssueSet,
                              Semester,
                              SemesterField)
from phonenumber_field import phonenumber
import re


class Application(Model):
    """An applicant's entire response."""

    applicant = ForeignKey('ApplicantProfile', on_delete=CASCADE)
    due_at = DateTimeField()
    address = TextField(blank=True)
    phone = TextField(blank=True)
    psu_email = TextField(blank=True)
    preferred_email = TextField(blank=True)
    psu_id = TextField(blank=True)
    major = TextField(blank=True)
    emch_minor = BooleanField(default=False)
    semester_initiated = SemesterField(null=True, blank=True)
    semester_graduating = SemesterField(null=True, blank=True)
    cumulative_gpa = FloatField(null=True, blank=True)
    semester_gpa = FloatField(null=True, blank=True)
    in_state_tuition = BooleanField(default=False)
    additional_remarks = TextField(blank=True)
    submitted = BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.submitted:
            issues = CustomValidationIssueSet()
            self.custom_validate(issues)
            if len(issues) > 0:
                # last line of defense; should never have to be raised
                raise ValueError('cannot submit Application with issues!')
        super(Application, self).save(*args, **kwargs)

    def _custom_validate_fields(self, issues):
        """Custom validation rules for fields within Application"""

        common_section = 'basicinfo'

        if self.address is None or self.address == '':
            issues.create(section=common_section,
                          field='address',
                          code='required')

        if self.phone is None or self.phone == '':
            issues.create(section=common_section,
                          field='phone',
                          code='required')
        elif not phonenumber.to_python(self.phone).is_valid():
            issues.create(section=common_section,
                          field='phone',
                          code='invalid')

        if self.psu_email is None or self.psu_email == '':
            issues.create(section=common_section,
                          field='psu_email',
                          code='required')
        else:
            try:
                EmailValidator()(self.psu_email)
                if not self.psu_email.endswith('@psu.edu'):
                    issues.create(section=common_section,
                                  field='psu_email',
                                  code='prohibited')
            except ValidationError:
                issues.create(section=common_section,
                            field='psu_email',
                            code='invalid')

        if self.preferred_email == '':
            # preferred_email is assumed to be psu_email if blank
            pass
        else:
            try:
                EmailValidator()(self.preferred_email)
            except ValidationError:
                issues.create(section=common_section,
                            field='preferred_email',
                            code='invalid')

        if self.psu_id is None or self.psu_id == '':
            issues.create(section=common_section,
                          field='psu_id',
                          code='required')
        elif not re.match(r'^9\d{8}$', self.psu_id):
            issues.create(section=common_section,
                          field='psu_id',
                          code='invalid')

        if self.major is None or self.major == '':
            issues.create(section=common_section,
                          field='major',
                          code='required')

        if self.semester_initiated is None:
            issues.create(section=common_section,
                          field='semester_initiated',
                          code='required')
        elif self.semester_initiated > Semester(self.due_at.date()):
            issues.create(section=common_section,
                          field='semester_initiated',
                          code='invalid')
        elif self.semester_initiated < Semester(('Spring', 1928)):
            issues.create(section=common_section,
                          field='semester_initiated',
                          code='invalid')

        if self.semester_graduating is None:
            issues.create(section=common_section,
                          field='semester_graduating',
                          code='required')
        elif self.semester_graduating < Semester(self.due_at.date()):
            issues.create(section=common_section,
                          field='semester_graduating',
                          code='invalid')
        elif self.semester_graduating > Semester(('Fall', 2099)):
            issues.create(section=common_section,
                          field='semester_graduating',
                          code='invalid')

        if self.cumulative_gpa == None:
            issues.create(section=common_section,
                          field='cumulative_gpa',
                          code='required')
        elif (self.cumulative_gpa < 0.0 or self.cumulative_gpa > 4.0):
            issues.create(section=common_section,
                          field='cumulative_gpa',
                          code='invalid')

        if self.semester_gpa == None:
            issues.create(section=common_section,
                          field='semester_gpa',
                          code='required')
        elif (self.semester_gpa < 0.0 or self.semester_gpa > 4.0):
            issues.create(section=common_section,
                          field='semester_gpa',
                          code='invalid')

    def custom_validate(self, issues):
        """Validate entire Application using custom logic.

        This custom validation component is required because Django's
        validation is simultaneously too strictly applied (i.e., model forms
        cannot be saved without validation) and too loosely defined (i.e.,
        ValidationErrors don't contain enough structured data).
        """

        if not isinstance(issues, CustomValidationIssueSet):
            raise TypeError('need a CustomValidationIssueSet')

        self._custom_validate_fields(issues)
        section_managers = [freemoney.models.Award.objects,
                            freemoney.models.Feedback.objects]
        for section_manager in section_managers:
            section_manager.custom_validate_for_application(self, issues)

        for financial_aid in self.financialaid_set.iterator():
            financial_aid.custom_validate(issues)
