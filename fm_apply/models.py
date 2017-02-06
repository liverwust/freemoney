import datetime
import decimal
from django.core.exceptions import ValidationError
from django.core.validators import (MinValueValidator,
                                    MaxValueValidator,
                                    MinLengthValidator,
                                    RegexValidator)
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class SemesterField(models.DateField):
    """Converts between semester designations (Fall '17) and dates.

    A semester designation is represented as a tuple like ('SP', 2016). A
    date, for the purposes of this field, should fall approximately near the
    middle of the semester. Particularly, Spring is converted to Jan 1 by this
    class, and Fall to Oct 1.
    """
    description = "Semester designation (Oct 1 for Fall, Jan 1 for Spring)"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _date_to_semester(self, date):
        if (date >= datetime.date(date.year, 1, 1) and    # Jan 1
            date <= datetime.date(date.year, 4, 1)):      # Apr 1
            return ('Spring', date.year)
        elif (date >= datetime.date(date.year, 8, 15) and # Aug 15
              date <= datetime.date(date.year, 12, 1)):
            return ('Fall', date.year)
        else:
            raise ValidationError('invalid or ambiguous date for semester')

    def _semester_to_date(self, semester_tuple):
        semester, year = semester_tuple
        if semester.lower() in ('fall', 'fa'):
            return datetime.date(year, 10, 1)  # October 1
        elif semester.lower() in ('spring', 'sp'):
            return datetime.date(year, 1, 1)   # January 1
        else:
            raise ValidationError('invalid semester designation')

    def from_db_value(self, value):
        date = super().from_db_value(value)
        return self._date_to_semester(date)

    def to_python(self, value):
        date = super().to_python(value)
        return self._date_to_semester(date)

    def get_prep_value(self, value):
        date = self._semester_to_date(value)
        return super().get_prep_value(date)


class ApplicantResponse(models.Model):
    """An applicant's entire response, including dynamic elements."""

    # Administrative
    submitted = models.BooleanField(default=False)
    #created_timestamp = models.DateTimeField()
    #due_timestamp = models.DateTimeField()
    #semester_for = SemesterField()

    # Actual response elements (no per-field validation)
    name = models.CharField(max_length=255, blank=True)
    address = models.TextField(blank=True)
    phone = PhoneNumberField(blank=True)
    psu_email = models.EmailField(blank=True)
    preferred_email = models.EmailField(blank=True)
    psu_id = models.CharField(max_length=9, blank=True)
    semester_initiated = SemesterField(null=True)
    semester_graduating = SemesterField(null=True)
    cumulative_gpa = models.DecimalField(max_digits=3,
                                         decimal_places=2,
                                         null=True)
    semester_gpa = models.DecimalField(max_digits=3,
                                       decimal_places=2,
                                       null=True)
    in_state_tuition = models.NullBooleanField()

    def soft_validate(self):
        """Perform "soft" validation, as opposed to DB-level validation.

        An ApplicantResponse can either be submitted, in which case all of its
        fields should be valid according to the rules defined below, or
        unsubmitted, in which case most of its fields can be blank.

        For the purpose of indicating progress, it is useful to know which
        fields are invalid even when not saving data to the DB.
        """

        def do(field_name, validators):
            value = getattr(self, field_name)
            error_dict = {field_name: []}
            if isinstance(validators, list):
                validator_list = validators
            else:
                validator_list = [validators]
            for validator in validator_list:
                try:
                    validator(value)
                except ValidationError as e:
                    error_dict[field_name].append(str(e))
            if len(error_dict[field_name]) > 0:
                raise ValidationError(error_dict)

        def not_null(message):
            def not_null_validator(value):
                if value == None:
                    raise ValidationError(message)
            return not_null_validator

        do('name', [MinLengthValidator(1, 'name cannot be blank')])
        do('address', [MinLengthValidator(1, 'address cannot be blank')])
        do('phone', [MinLengthValidator(1, 'phone number cannot be blank')])
        do('psu_email', [MinLengthValidator(1, 'PSU email is required')])
        do('psu_id', [RegexValidator(r'^9\d{8}$', 'PSU ID: 9xxxxxxxx')])
        do('semester_initiated', [not_null('initiation semester required')])
        do('semester_graduating', [not_null('graduation semester required')])
        do('cumulative_gpa', [MinValueValidator('0.00'),
                              MaxValueValidator('4.00')])
        do('semester_gpa', [MinValueValidator('0.00'),
                            MaxValueValidator('4.00')])
        do('in_state_tuition', [not_null('must select in/out state tuition')])

    def clean(self):
        if self.submitted:
            self.soft_validate()


class FinancialAidRecord(models.Model):
    """An ApplicantResponse record describing sources of financial aid."""

    response = models.ForeignKey(ApplicantResponse, on_delete=models.CASCADE)
    aid_type = models.CharField(max_length=50)
    description = models.CharField(max_length=255)
    amount_per_year = models.DecimalField(max_digits=7, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()


class ActivityRecord(models.Model):
    """An ApplicantResponse record describing activities & accomplishments."""

    response = models.ForeignKey(ApplicantResponse, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=50)
    description = models.CharField(max_length=255)
    accomplishments = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()


class EssayResponse(models.Model):
    """An ApplicantResponse record containing an essay."""

    response = models.ForeignKey(ApplicantResponse, on_delete=models.CASCADE)
    prompt = models.ForeignKey('EssayPrompt', on_delete=models.CASCADE)
    text = models.TextField()


class VersionedDescription(models.Model):
    """Generic base class for long descriptions which can be modified.

    The reason to "version" a long description (e.g., an essay prompt) is to
    ensure that an applicant's response can be forever linked with the
    *original* version of the text which he saw. Reworking the text of such a
    prompt could alter the context of the response.
    """

    permanent_id = models.SlugField(unique=True)
    created_timestamp = models.DateTimeField()
    previous_version = models.ForeignKey('self',
                                         null=True,
                                         on_delete=models.CASCADE)

    class Meta:
        abstract = True


class EssayPrompt(VersionedDescription):
    """The prompt for an essay question."""

    response_set = models.ManyToManyField(ApplicantResponse,
                                          through=EssayResponse)
    prompt = models.TextField()


class ScholarshipAward(VersionedDescription):
    """Represents a particular scholarship award."""

    response_set = models.ManyToManyField(ApplicantResponse)
    name = models.CharField(max_length=255)
    description = models.TextField()
