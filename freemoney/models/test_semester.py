import datetime
from django.test import TestCase
from freemoney.models import Semester


class SemesterTestCase(TestCase):
    """Test Semester class conversions and comparisons in isolation"""

    def setUp(self):
        self.spring_min = datetime.date(year=2017,
                                        month=1,   # January
                                        day=1)
        self.spring_max = datetime.date(year=2017,
                                        month=5,   # May
                                        day=31)
        self.fall_min   = datetime.date(year=2017,
                                        month=8,   # August
                                        day=1)
        self.fall_max   = datetime.date(year=2017,
                                        month=12,  # December
                                        day=31)

    def assertBetween(self, first, second, third, msg=None):
        self.assertLessEqual(first, second, msg)
        self.assertLessEqual(second, third, msg)

    def test_constructors(self):
        """Ensure that the constructor accepts all advertised formats"""
        a = Semester('Spring 2017')
        b = Semester(('Spring', 2017))
        c = Semester(datetime.datetime(2017, 2, 25))
        d = Semester(a)
        self.assertEqual(a, b)
        self.assertEqual(b, c)
        self.assertEqual(c, d)

    def test_SP16(self):
        """Check that the "SP17"-style string constructor works"""
        s = Semester('SP17')
        self.assertBetween(self.spring_min, s.date, self.spring_max)
        self.assertBetween(Semester(self.spring_min),
                           Semester(s),
                           Semester(self.spring_max))
        s = Semester('FA17')
        self.assertBetween(Semester(self.fall_min),
                           Semester(s.date),
                           Semester(self.fall_max))

    def test_Spring_2017(self):
        """Check that the "Spring 2017"-style string constructor works"""
        s = Semester('Spring 2017')
        self.assertBetween(Semester(self.spring_min),
                           Semester(s.date),
                           Semester(self.spring_max))
        s = Semester('Fall 2017')
        self.assertBetween(Semester(self.fall_min),
                           Semester(s),
                           Semester(self.fall_max))

    def test_Spring_2017(self):
        """Check that the ("spring", 2017) tuple constructor works"""
        s = Semester(('Spring', 2017))
        self.assertBetween(self.spring_min, s.date, self.spring_max)
        s = Semester(('fa', 2017))
        self.assertBetween(Semester(self.fall_min),
                           s,
                           Semester(self.fall_max))

    def test_date(self):
        """Check that the date constructor works"""
        for spring_date in [self.spring_min,
                            datetime.date(2017, 3, 15),
                            self.spring_max]:
            self.assertEqual('Spring 2017', str(Semester(spring_date)))
        for fall_date in [self.fall_min,
                          datetime.date(2017, 10, 15),
                          self.fall_max]:
            self.assertEqual('Fall 2017', str(Semester(fall_date)))

    def test_summer_date(self):
        """Check that an invalid date (e.g., during Summer 2017) fails"""
        with self.assertRaises(ValueError):
            Semester(datetime.date(2017, 6, 30))
