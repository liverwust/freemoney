from django.test import TestCase
from freemoney.models import (CustomValidationIssue,
                              CustomValidationIssueSet)


class CustomValidationTestCase(TestCase):
    """Verify the basic functionality of custom validation"""

    def test_invalid_specifications(self):
        """Try various ways of incorrectly adding issues to the manager"""

        issues = CustomValidationIssueSet()
        with self.assertRaises(TypeError):
            # incorrect type for field
            issues.create(section='test', field=5, subfield=5, code='invalid')

        with self.assertRaises(KeyError):
            # nonexistent code
            issues.create(section='t', field='t', code='FALSE')

        with self.assertRaises(ValueError):
            # subfield without a section
            issues.create(subfield=5, code='invalid')

    def test_all_for_section(self):
        """Add a bunch of issues on several sections, and check one section"""

        issues = CustomValidationIssueSet()
        issues.create(section='section1', code='prohibited')
        issues.create(section='section2', field='a', code='min-length')
        issues.create(section='section3', field='b', subfield=5,
                      code='invalid')
        issues.create(section='section1', field='c', subfield=1,
                      code='max-length')

        self.assertEqual(2, len(issues.search(section='section1')))

    def test_search_by_code(self):
        """Add a bunch of tests and filter by code"""

        issues = CustomValidationIssueSet()
        issues.create(section='section1', code='prohibited')
        issues.create(section='section1', field='a', code='invalid')
        issues.create(section='section1', field='b', code='invalid')
        issues.create(section='section1', field='c', code='min-length')
        issues.create(section='section2', field='b', code='min-length')
        issues.create(section='section2', field='c', code='prohibited')
        issues.create(section='section3', code='invalid')
        issues.create(code='max-length')

        self.assertEqual(3, len(issues.search(code='invalid')))

    def test_aggregate(self):
        """Add and aggregate several issues for a single field"""

        issues = CustomValidationIssueSet()
        issues.create(section='section1', field='c', code='min-length')
        issues.create(section='section2', field='c', code='min-length')
        issues.create(section='section2', field='c', code='prohibited')
        issues.create(section='section2', field='c', code='invalid')
        issues.create(section='section3', code='prohibited')

        self.assertSetEqual(set(['min-length', 'prohibited', 'invalid']),
                            set(issues.search(section='section2',
                                              field='c',
                                              aggregate=True)))

    def test_hierarchy(self):
        """Verify that it is impossible to use an invalid hierarchy spec"""

        issues = CustomValidationIssueSet()

        with self.assertRaises(ValueError):
            issues.create(field='noparent', code='invalid')
        with self.assertRaises(ValueError):
            issues.create(subfield=5, code='invalid')
        with self.assertRaises(ValueError):
            issues.create(section='grandparent', subfield=4,
                          code='invalid')
        self.assertEqual(0, len(issues))

        with self.assertRaises(ValueError):
            issues.search(section=CustomValidationIssueSet.GLOBAL,
                          field=CustomValidationIssueSet.GLOBAL,
                          subfield=5)
        with self.assertRaises(ValueError):
            issues.search(field=CustomValidationIssueSet.GLOBAL)
        with self.assertRaises(ValueError):
            issues.search(field='noparent')
        with self.assertRaises(ValueError):
            issues.search(subfield=5)
        with self.assertRaises(ValueError):
            issues.search(section='grandparent', subfield=4)
        with self.assertRaises(ValueError):
            issues.search(section='grandparent',
                          field=CustomValidationIssueSet.GLOBAL,
                          subfield=4)
