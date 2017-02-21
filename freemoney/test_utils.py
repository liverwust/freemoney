import datetime
from freemoney.utils import Semester
import unittest


class SemesterTestCase(unittest.TestCase):
    """Test converting between semester designations and dates."""

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
        a = Semester('Spring 2017')
        b = Semester(('Spring', 2017))
        c = Semester(datetime.datetime(2017, 2, 25))
        d = Semester(a)
        self.assertEqual(a, b)
        self.assertEqual(b, c)
        self.assertEqual(c, d)

    def test_SP16(self):
        s = Semester('SP17')
        self.assertBetween(self.spring_min, s.date, self.spring_max)
        self.assertBetween(Semester(self.spring_min),
                           s.date,
                           Semester(self.spring_max))
        s = Semester('FA17')
        self.assertBetween(self.fall_min, s.date, self.fall_max)

    def test_Spring_2017(self):
        s = Semester('Spring 2017')
        self.assertBetween(self.spring_min, s.date, self.spring_max)
        s = Semester('Fall 2017')
        self.assertBetween(Semester(self.fall_min),
                           s,
                           Semester(self.fall_max))

    def test_reverse(self):
        for spring_date in [self.spring_min,
                            datetime.date(2017, 3, 15),
                            self.spring_max]:
            self.assertEqual('Spring 2017', str(Semester(spring_date)))
        for fall_date in [self.fall_min,
                          datetime.date(2017, 10, 15),
                          self.fall_max]:
            self.assertEqual('Fall 2017', str(Semester(fall_date)))
        with self.assertRaises(ValueError):
            # summer date
            Semester(datetime.date(2017, 6, 30))
