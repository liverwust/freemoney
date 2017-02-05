import datetime
import decimal
from django.core.exceptions import ValidationError
from django.core.validators import (MinValueValidator,
                                    MaxValueValidator,
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
    created_timestamp = models.DateTimeField()
    due_timestamp = models.DateTimeField()
    semester_for = SemesterField()

    # Actual response elements
    name = models.CharField(max_length=255)
    address = models.TextField()
    phone = PhoneNumberField()
    psu_email = models.EmailField()
    preferred_email = models.EmailField(blank=True)
    psu_id = models.CharField(
            max_length=9,
            validators=[RegexValidator(regex=r'^9\d{8}$')]
    )
    semester_initiated = SemesterField()
    semester_graduating = SemesterField()
    cumulative_gpa = models.DecimalField(
            max_digits=3,
            decimal_places=2,
            validators=[MinValueValidator('0.00'), MaxValueValidator('4.00')]
    )
    semester_gpa = models.DecimalField(
            max_digits=3,
            decimal_places=2,
            validators=[MinValueValidator('0.00'), MaxValueValidator('4.00')]
    )
    in_state_tuition = models.BooleanField()


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
