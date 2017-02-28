from django.core import exceptions
from django.db import models
import datetime
import functools
import re


@functools.total_ordering
class Semester:
    """Represents the pairing of a semester and a year.
    
    A Semester object is immutable. It can be compared to other Semesters.

    The constructor accepts all of the following:
      * Another Semester object
      * A datetime.date
      * A string of the form "Spring 2017" or "FA11"
      * A tuple like ("fall", 2016)
    """

    STRUCTURE_REGEX = re.compile(r'^([a-zA-Z]+)\s*(\d{2}|\d{4})$')
    SPRING_REGEX = re.compile(r'^sp(?:ring)?$', re.IGNORECASE)
    FALL_REGEX = re.compile(r'^fa(?:ll)?$', re.IGNORECASE)

    def __init__(self, value):
        if isinstance(value, Semester):
            self._inner_date = value._inner_date
        elif isinstance(value, datetime.date):
            semester = Semester.month_day_to_semester(value.month, value.day)
            month, day = Semester.semester_to_month_day(semester)
            self._inner_date = datetime.date(value.year, month, day)
        elif isinstance(value, str):
            match = Semester.STRUCTURE_REGEX.match(value)
            if match is None:
                raise ValueError('invalid semester/year string')
            elif match.group(1) is None or match.group(2) is None:
                raise ValueError('semester/year string is missing a piece')
            else:
                semester, year = match.group(1), int(match.group(2))
                if year < 100:
                    year += 2000     # from two-digit year to four-digit
                month, day = Semester.semester_to_month_day(semester)
                self._inner_date = datetime.date(year, month, day)
        elif isinstance(value, tuple):
            semester, year = value[0], int(value[1])
            if year < 100:
                year += 2000         # from two-digit year to four-digit
            month, day = Semester.semester_to_month_day(semester)
            self._inner_date = datetime.date(year, month, day)
        else:
            raise TypeError('invalid type for semester descriptor')

    @property
    def is_spring(self):
        return (Semester(('Spring', self.date.year)) == self)

    @property
    def is_fall(self):
        return (Semester(('Fall', self.date.year)) == self)

    @property
    def date(self):
        return self._inner_date

    def __str__(self):
        semester = Semester.month_day_to_semester(self._inner_date.month,
                                                  self._inner_date.day)
        return '{} {}'.format(semester, self._inner_date.year)

    def __eq__(self, other):
        if isinstance(other, Semester):
            return self.date == Semester(other).date
        else:
            return False

    def __gt__(self, other):
        if isinstance(other, Semester):
            return self.date > Semester(other).date
        else:
            raise TypeError('can only order Semesters with other Semesters')

    @staticmethod
    def month_day_to_semester(month, day):
        arbitrary_year = 2000
        input_date = datetime.date(arbitrary_year, month, day)
        if (input_date >= datetime.date(arbitrary_year, 1, 1) and
            input_date <= datetime.date(arbitrary_year, 5, 31)):
            return 'Spring'
        elif (input_date >= datetime.date(arbitrary_year, 8, 1) and
              input_date <= datetime.date(arbitrary_year, 12, 31)):
            return 'Fall'
        else:
            raise ValueError('month/day does not correspond to a semester')

    @staticmethod
    def semester_to_month_day(semester):
        # these month/day pairs are arbitrary, but sufficient
        if Semester.SPRING_REGEX.match(semester):
            return (2, 1)   # month=February, day=1
        elif Semester.FALL_REGEX.match(semester):
            return (9, 1)   # month=September, day=1
        else:
            raise ValueError('malformed semester descriptor')


class SemesterField(models.DateField):

    description = "Represents the pairing of a semester and a year in the DB"

    def from_db_value(self, value, expression_, connection_, context_):
        # Note: DateField doesn't define from_db_value, so no super() call
        if value is None:
            return value
        else:
            # Don't catch exceptions; data from DB should always be valid!
            return Semester(value)

    def get_prep_value(self, value):
        value = super(SemesterField, self).get_prep_value(value)
        if value is None:
            return value
        else:
            return value.date

    def to_python(self, value):
        if isinstance(value, (Semester, type(None))):
            return value

        else:
            try:
                # Assuming a date-like value, try to normalize it first
                value = super(SemesterField, self).to_python(value)
            except exceptions.ValidationError as exc:
                if exc.code == 'invalid_date' and exc.params['value'] == value:
                    # value is indeed a date(time) but is malformed; reraise
                    raise
                elif exc.code == 'invalid' and exc.params['value'] == value:
                    # value wasn't recognized by parse_date; try w/ Semester
                    # (e.g., it might be something like "Spring 2016")
                    pass
                else:
                    # something else is amiss; reraise
                    raise

            try:
                # At this point, value should be a date or a "SP16"-like string
                value = Semester(value)
            except ValueError as exc:
                raise exceptions.ValidationError(
                        'malformed or invalid semester specification: %(err)s',
                        code='invalid_semester',
                        params={'err': str(exc)}
                )

            return value

    def value_to_string(self, obj):
        val = self.value_from_object(obj)
        val = self.get_prep_value(val)
        return str(val)

    def formfield(self, **kwargs):
        from freemoney.views import SemesterFormField
        defaults = {'form_class': SemesterFormField}
        defaults.update(kwargs)
        return super(SemesterField, self).formfield(**defaults)
