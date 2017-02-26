import datetime
import functools
from io import BytesIO
from lxml import etree
import re


@functools.total_ordering
class Semester:
    """Represents the pairing of a semester and a year."""

    STRUCTURE_REGEX = re.compile(r'^([a-zA-Z]+)?\s*(\d{2}|\d{4})?$')
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
    def date(self):
        return self._inner_date

    def __str__(self):
        semester = Semester.month_day_to_semester(self._inner_date.month,
                                                  self._inner_date.day)
        return '{} {}'.format(semester, self._inner_date.year)

    def __eq__(self, other):
        return self.date == Semester(other).date

    def __gt__(self, other):
        return self.date > Semester(other).date

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


def parse_formset_management_form(page_content):
    """Extract the <input> values required for Django formset postback."""
    postdata = {}
    name_re = re.compile(r'^([^-]*)-(TOTAL|INITIAL|MIN_NUM|MAX_NUM)_FORMS$')
    ET = etree.parse(BytesIO(page_content), etree.HTMLParser())
    for element in ET.findall(r".//form//input[@type='hidden']"):
        match = name_re.match(element.get('name'))
        if match != None:
            form_name, field_meaning = match.group(1), match.group(2)
            postdata[match.group(0)] = element.get('value')
    return postdata
