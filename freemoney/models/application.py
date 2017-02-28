import datetime
from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import (MinValueValidator,
                                    MaxValueValidator,
                                    RegexValidator)
from django.db.models import (Model,
                              CASCADE,
                              BooleanField,
                              CharField,
                              DecimalField,
                              EmailField,
                              ForeignKey,
                              TextField)
from freemoney.models import (Semester,
                              SemesterModelField)
from phonenumber_field.modelfields import PhoneNumberField


class Application(Model):
    """An applicant's entire response."""

    submitted = BooleanField(default=False)
    applicant = ForeignKey('ApplicantProfile', on_delete=CASCADE)
    application_semester = SemesterModelField()

    # Contact information
    address = TextField('permanent mailing address',
                        help_text='Where can we mail your money (by check)?')
    phone = PhoneNumberField('primary phone number',
                             help_text='Cell phone is acceptable')
    psu_email = EmailField('university e-mail address',
                           help_text='This is your psu.edu e-mail',
                           validators=[RegexValidator(r'@psu.edu$')])
    preferred_email = EmailField('preferred e-mail address',
                                 help_text='Leave blank if same as above')
    psu_id = CharField('university ID number',
                       help_text='Nine digits: 9xxxxxxxx',
                       max_length=9,
                       validators=[RegexValidator(r'^(?:9\d{8})?$')])
    outside_pa = BooleanField('out-of-state resident',
                              default=False,
                              help_text='Do you pay out-of-state tuition?')

    # Membership information
    semester_initiated = SemesterModelField(null=True)
    semester_graduating = SemesterModelField(null=True)

    # Scholastic information
    cumulative_gpa = DecimalField('cumulative GPA',
            help_text='Cumulative GPA as of the end of last semester',
            max_digits=3,
            decimal_places=2,
            null=True,
            validators=[MinValueValidator(Decimal("0.00")),
                        MaxValueValidator(Decimal("4.00"))])
    semester_gpa = DecimalField('semester GPA',
            help_text='Semester GPA for the most recent completed semester',
            max_digits=3,
            decimal_places=2,
            null=True,
            validators=[MinValueValidator(Decimal("0.00")),
                        MaxValueValidator(Decimal("4.00"))])
    in_state_tuition = models.NullBooleanField(
            'in-state tuition',
            help_text='Do you pay the reduced tuition rate for PA residents?',
            blank=True
    )

    # Applicant responses
    additional_remarks = TextField(blank=True)

    def custom_validate(self):
        """Validate model fields, self-consistency, and uniqueness."""

        error_dict = {}
        if self.submitted:
            try:
                self._deferred_clean_fields()
            except ValidationError as exc:
                error_dict = exc.error_dict

            if len(self.scholarshipaward_set.all()) < 1:
                key = 'scholarshipaward_set'
                message = 'need to select at least one scholarship award'
                error_dict[key] = ValidationError(message, code='invalid')

            if (self.reviewedpeer_set.count() <
                settings.FREEMONEY_MIN_FEEDBACK):
                key = 'reviewedpeer_set'
                message = 'need at least {} peer feedbacks'.format(
                        settings.FREEMONEY_MIN_FEEDBACK
                )
                error_dict[key] = ValidationError(message, code='invalid')
        if error_dict != {}:
            raise ValidationError(error_dict)

    def _deferred_clean_fields(self):
        errors = {}

        if self.name == '':
            errors['name'] = ('name cannot be left blank',
                                'required')

        if self.address == '':
            errors['address'] = ('address cannot be left blank',
                                    'required')

        if self.phone == '':
            errors['phone'] = ('phone number cannot be left blank',
                                'required')

        if self.psu_email == '':
            errors['psu_email'] = ('PSU email cannot be left blank',
                                    'required')

        if self.psu_id == '':
            errors['psu_id'] = ('PSU ID cannot be left blank',
                                'required')

        if self.date_initiated == None:
            errors['date_initiated'] = ('initiation date is required',
                                        'required')
        elif Semester(self.date_initiated) > Semester(self.due_at):
            errors['date_initiated'] = ('initiated date in the future',
                                        'invalid')

        if self.date_graduating == None:
            errors['date_graduating'] = ('est. graduation date is required',
                                        'required')
        elif Semester(self.date_graduating) < Semester(self.due_at):
            errors['date_graduating'] = ('graduation date in the past',
                                            'invalid')

        if self.cumulative_gpa == None:
            errors['cumulative_gpa'] = ('cumulative GPA is required',
                                        'required')
        elif (self.cumulative_gpa < decimal.Decimal('0.00') or
                self.cumulative_gpa > decimal.Decimal('4.00')):
            errors['cumulative_gpa'] = ('cumulative GPA too high/low',
                                        'invalid')

        if self.semester_gpa == None:
            errors['semester_gpa'] = ('semester GPA is required',
                                        'required')
        elif (self.semester_gpa < decimal.Decimal('0.00') or
                self.semester_gpa > decimal.Decimal('4.00')):
            errors['semester_gpa'] = ('semester GPA too high/low',
                                        'invalid')

        if self.in_state_tuition == None:
            errors['in_state_tuition'] = ('select in/out state tuition',
                                            'required')
        if self.peerfeedback_set.count() < settings.FREEMONEY_MIN_FEEDBACK:
            errors.append(ValidationError(
                    'Need %(min)s peer feedback entries; only %(curr)s given',
                    code='feedback:min_length',
                    params={'min': str(settings.FREEMONEY_MIN_FEEDBACK),
                            'curr': str(self.peerfeedback_set.count())}
            ))

        if (self.semester_initiated != None and
            self.semester_initiated > self.application_semester):
            errors.append(ValidationError({
                    'semester_initiated': ValidationError(
                            'Semester of initiation is in the future',
                            code='invalid'
                    )
            }))

        if (self.semester_graduating != None and
            self.semester_graduating < self.application_semester):
            errors.append(ValidationError({
                    'semester_graduating': ValidationError(
                            'Semester of graduation is in the past',
                            code='invalid'
                    )
            }))

        for field in errors.keys():
            errors[field] = ValidationError(errors[field][0],
                                            code=errors[field][1])
        if len(errors) > 0:
            raise ValidationError(errors)
