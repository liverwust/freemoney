from datetime import datetime, timezone
from django.contrib.auth import get_user_model
from django.test import TestCase
from freemoney.models import (ApplicantProfile,
                              Application,
                              CustomValidationIssueSet,
                              FinancialAid,
                              Semester)


class FinancialAidApplicationTests(TestCase):
    """Test the validation of FinancialAid records within an Application"""

    def setUp(self):
        self.applicant = ApplicantProfile.objects.create(
                user=get_user_model().objects.create_user(
                        username='test1234@example.com',
                        password='pass1234'
                ),
                must_change_password=False
        )
        self.application = Application.objects.create(
                applicant=self.applicant,
                due_at = datetime(2016, 11, 15, tzinfo=timezone.utc)
        )

    def test_required_fields(self):
        aid = FinancialAid.objects.create(
                application=self.application,
                aid_type='test',
                provider='',
                end_date=None,
                installment_frequency='yearly',
                installment_amount=1.00
        )

        # no provider
        issues = CustomValidationIssueSet()
        self.application.custom_validate(issues)
        found_issues = issues.search(section='finaid',
                                     field='[records]',
                                     code='required')
        self.assertEqual(len(found_issues), 1)
        first_iter = iter(found_issues)
        self.assertNotEqual(next(first_iter).subfield, None)

        # no installment frequency
        aid.provider = 'test'
        aid.installment_frequency = ''
        aid.full_clean()
        aid.save()
        issues = CustomValidationIssueSet()
        self.application.custom_validate(issues)
        found_issues = issues.search(section='finaid',
                                     field='[records]',
                                     code='required')
        self.assertEqual(len(found_issues), 1)
        first_iter = iter(found_issues)
        self.assertNotEqual(next(first_iter).subfield, None)

        # no aid_type
        aid.installment_frequency = 'yearly'
        aid.aid_type = ''
        aid.full_clean()
        aid.save()
        issues = CustomValidationIssueSet()
        self.application.custom_validate(issues)
        found_issues = issues.search(section='finaid',
                                     field='[records]',
                                     code='required')
        self.assertEqual(len(found_issues), 1)
        first_iter = iter(found_issues)
        self.assertNotEqual(next(first_iter).subfield, None)

        # all required fields (and no optional fields) present
        aid.aid_type='test'
        aid.full_clean()
        aid.save()
        issues = CustomValidationIssueSet()
        self.application.custom_validate(issues)
        self.assertEqual(len(issues.search(section='finaid')), 0)

    def test_valid_installments(self):
        aid = FinancialAid.objects.create(
                application=self.application,
                aid_type='test',
                provider='testprovider',
                end_date=None,
                installment_frequency='yearly',
                installment_amount=-1.00,
        )

        # too small (negative)
        issues = CustomValidationIssueSet()
        self.application.custom_validate(issues)
        found_issues = issues.search(section='finaid',
                                     field='[records]',
                                     code='invalid')
        self.assertEqual(len(found_issues), 1)
        first_iter = iter(found_issues)
        self.assertNotEqual(next(first_iter).subfield, None)

        # too large
        aid.installment_amount = 1000000.00
        aid.full_clean()
        aid.save()
        issues = CustomValidationIssueSet()
        self.application.custom_validate(issues)
        found_issues = issues.search(section='finaid',
                                     field='[records]',
                                     code='invalid')
        self.assertEqual(len(found_issues), 1)
        first_iter = iter(found_issues)
        self.assertNotEqual(next(first_iter).subfield, None)

        # just right
        aid.installment_amount = 5000.00
        aid.full_clean()
        aid.save()
        issues = CustomValidationIssueSet()
        self.application.custom_validate(issues)
        self.assertEqual(len(issues.search(section='finaid',
                                           field='[records]',
                                           code='invalid')), 0)

    def test_yearly_amount_conversions(self):
        aid = FinancialAid.objects.create(
                application=self.application,
                aid_type='test',
                provider='testprovider',
                end_date=None,
                installment_frequency='yearly',
                installment_amount=500.00
        )
        self.assertAlmostEqual(500.00, aid.yearly_amount)

        aid.installment_frequency = 'monthly'
        aid.full_clean()
        aid.save()
        self.assertAlmostEqual(6000.00, aid.yearly_amount)

        aid.installment_frequency = 'semesterly'
        aid.full_clean()
        aid.save()
        self.assertAlmostEqual(1000.00, aid.yearly_amount)

        aid.installment_frequency = 'semeserly' # misspelled
        aid.full_clean()
        aid.save()
        with self.assertRaises(ValueError):
            aid.yearly_amount
