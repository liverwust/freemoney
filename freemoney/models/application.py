import datetime
import decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import (MinValueValidator,
                                    MaxValueValidator,
                                    MinLengthValidator,
                                    RegexValidator)
from django.db import models
from freemoney.utils import Semester
from phonenumber_field.modelfields import PhoneNumberField


class Application(models.Model):
    """An applicant's entire response."""

    # Administrative
    submitted = models.BooleanField(default=False)
    applicant = models.ForeignKey('ApplicantProfile', on_delete=models.CASCADE)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    due_at = models.DateTimeField()

    # Actual response elements (see the clean method for further validations)
    name = models.CharField(
            'full name',
            max_length=255,
            blank=True
    )
    address = models.TextField(
            'permanent mailing address',
            blank=True
    )
    phone = PhoneNumberField(
            'primary phone number',
            help_text='Cell phone is acceptable',
            blank=True
    )
    psu_email = models.EmailField(
            'university e-mail address',
            help_text='This is your psu.edu e-mail',
            blank=True,
            validators=[RegexValidator(r'^(?:[^@]+@psu.edu)?$')]
    )
    preferred_email = models.EmailField(
            'preferred e-mail address',
            blank=True
    )
    psu_id = models.CharField(
            'university ID number',
            help_text='Nine digits: 9xxxxxxxx',
            max_length=9,
            blank=True,
            validators=[RegexValidator(r'^(?:9\d{8})?$')]
    )
    date_initiated = models.DateField(
            'date of initiation',
            null=True,
            blank=True
    )
    date_graduating = models.DateField(
            'planned graduation date',
            null=True,
            blank=True
    )
    cumulative_gpa = models.DecimalField(
            'cumulative GPA',
            max_digits=3,
            decimal_places=2,
            null=True,
            blank=True
    )
    semester_gpa = models.DecimalField(
            'last semester GPA',
            max_digits=3,
            decimal_places=2,
            null=True,
            blank=True
    )
    in_state_tuition = models.NullBooleanField(
            'in-state tuition',
            help_text='Do you pay the reduced tuition rate for PA residents?',
            blank=True
    )
    #TODO: revive User
    #reviewedpeer_set = models.ManyToManyField(auth.models.User,
    #                                          through='PeerFeedbackResponse')

    def save(self, *args, **kwargs):
        """Update timestamps on save."""
        if self.created_at == None:
            self.created_at = datetime.datetime.now(datetime.timezone.utc)
        self.updated_at = datetime.datetime.now(datetime.timezone.utc)
        super(Application, self).save(*args, **kwargs)

    def full_clean(self, force=False, *args, **kwargs):
        """Validate model fields, self-consistency, and uniqueness.

        Pass force=True to pretend that the response has been submitted for
        review, for the purposes of testing intermediate validity. See the
        clean() method docstring for the significance of this.
        """

        if force:
            original_status = self.submitted
            self.submitted = True
            super(Application, self).full_clean(*args, **kwargs)
            self.submitted = original_status
        else:
            super(Application, self).full_clean(*args, **kwargs)

    def clean(self):
        """Custom validation for an Application.

        An Application can either be submitted, in which case all of its
        fields should be valid according to the rules defined below, or
        unsubmitted, in which case many of its fields can be blank.
        """

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

#TODO: revive User
#            if (len(self.peerfeedbackresponse_set.all()) <
#                settings.MIN_PEERFEEDBACK):
#                key = 'peerfeedbackresponse_set'
#                message = 'need at least {} peer feedbacks'.format(
#                        settings.MIN_PEERFEEDBACK
#                )
#                error_dict[key] = ValidationError(message, code='invalid')
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

        for field in errors.keys():
            errors[field] = ValidationError(errors[field][0],
                                            code=errors[field][1])
        if len(errors) > 0:
            raise ValidationError(errors)
