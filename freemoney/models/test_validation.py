from django.test import TestCase
from freemoney.models import CustomValidationIssueManager


class CustomValidationTestCase(TestCase):
    """Verify the basic functionality of custom validation"""

    def test_invalid_specifications(self):
        """Try various ways of incorrectly adding issues to the manager"""

        issues = CustomValidationIssueManager()
        with self.assertRaises(TypeError):
            # incorrect type
            issues.add(page='test', field='test', code='invalid', message=5)

        with self.assertRaises(ValueError):
            # nonexistent code
            issues.add(page='t', field='t', code='FALSE', message='hello')

        with self.assertRaises(ValueError):
            # field without a page
            issues.add(field='test', code='invalid', message='hello')

    def test_all_for_page(self):
        """Add a bunch of issues on several pages, and check one page"""

        issues = CustomValidationIssueManager()
        issues.add(page='page1', code='prohibited', message='bad stuff')
        issues.add(page='page1', field='a', code='invalid', message='no')
        issues.add(page='page2', field='b', code='min-length', message='__')
        issues.add(code='max-length', message='too many issues reported')

        self.assertEqual(2, len(issues.for_page('page1', False)))
        self.assertEqual(3, len(issues.for_page('page1', True)))

    def test_limit_by_code(self):
        """Add a bunch of tests and filter by code"""

        issues = CustomValidationIssueManager()
        issues.add(page='page1', code='prohibited', message='bad stuff')
        issues.add(page='page1', field='a', code='invalid', message='no')
        issues.add(page='page1', field='b', code='invalid', message='no')
        issues.add(page='page1', field='c', code='min-length', message='no')
        issues.add(page='page2', field='b', code='min-length', message='__')
        issues.add(page='page2', field='c', code='prohibited', message='__')
        issues.add(page='page3', code='invalid', message='__')
        issues.add(code='max-length', message='too many issues reported')

        with issues.context(code='invalid') as proxy:
            proxy.add(page='page4', field='f', message='test')
            self.assertEqual(4, len(proxy.search()))

        self.assertEqual(4, len(issues.search(code='invalid')))

    def test_collapse_similar(self):
        """Add several issues for a single field"""

        issues = CustomValidationIssueManager()
        issues.add(page='page1', field='c', code='min-length', message='no')
        issues.add(page='page2', field='c', code='min-length', message='__')
        issues.add(page='page2', field='c', code='prohibited', message='!!')
        issues.add(page='page2', field='c', code='invalid', message='xx')
        issues.add(page='page2', field='c', code='invalid', message='dd')
        issues.add(page='page3', code='prohibited', message='__')

        page1_c = issues.search(page='page1', field='c')
        self.assertEqual(page1_c, [('page1', 'c', 'min-length', 'no')])
        page2_c = issues.search(page='page2', field='c')[0]
        self.assertSetEqual(set(list(zip(page2_c[2], page2_c[3]))),
                            set([('min-length', '__'), ('prohibited', '!!'),
                                 ('invalid', 'xx'), ('invalid', 'dd')]))
        page3_nofield = issues.search(page='page3')
        self.assertEqual(page3_nofield, [('page3', None, 'prohibited', '__')])

        self.assertEqual(2, len(issues.search(field='c')))
        self.assertEqual(5, len(issues.search(field='c', expand=True)))
