import datetime
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.validators import ValidationError
from django.test import TestCase
from freemoney.models import Application, ApplicantProfile, ScholarshipAward


class DeferredValidationTestCase(TestCase):
    """Test "deferred" validation of an Application.

    To enable applicant's responses to be persisted before they are completed
    and submitted for review, it is necessary to defer validation until the
    application is marked as complete. This test case verifies that fields
    aren't checked prematurely, but also that fields are *eventually* checked.
    """

    # this is a table: first column is field name,
    #                  second column is blank or None, depending on type
    #                  third column is an appropriate non-blank, non-None value
    FIELD_x_BLANK_x_VALID = [('name',             '',   'testname'),
                             ('address',          '',   'testaddress'),
                             ('phone',            '',   '2025551234'),
                             ('psu_email',        '',   'nobody@psu.edu'),
                             ('psu_id',           '',   '912345678'),
                             ('in_state_tuition', None, False),
                             ('semester_gpa',     None, Decimal('3.40')),
                             ('cumulative_gpa',   None, Decimal('3.40')),
                             ('date_graduating',  None, datetime.date(2020,
                                                                      12,
                                                                      12)),
                             ('date_initiated',   None, datetime.date(2010,
                                                                      12,
                                                                      5))]

    def setUp(self):
        self.test_user = get_user_model().objects.create_user(
                username='test@example.com',
                password='pass1234'
        )
        self.test_profile = ApplicantProfile.objects.create(
                user=self.test_user,
                must_change_password=False
        )
        self.due_at = (datetime.datetime.now(datetime.timezone.utc) +
                       datetime.timedelta(days=1))

    def assertBetween(self, first, second, third, msg=None):
        self.assertLessEqual(first, second, msg)
        self.assertLessEqual(second, third, msg)

    def test_timestamps(self):
        stamp1 = datetime.datetime.now(datetime.timezone.utc)
        ar = Application.objects.create(
                due_at=self.due_at,
                applicant=self.test_profile
        )
        stamp2 = datetime.datetime.now(datetime.timezone.utc)
        self.assertBetween(stamp1, ar.created_at, stamp2)
        self.assertBetween(stamp1, ar.updated_at, stamp2)
        ar.full_clean()
        ar.save()
        stamp3 = datetime.datetime.now(datetime.timezone.utc)
        self.assertBetween(stamp1, ar.created_at, stamp2)
        self.assertBetween(stamp2, ar.updated_at, stamp3)

    def test_mostly_blanks(self):
        ar = Application.objects.create(
                due_at=self.due_at,
                applicant=self.test_profile
        )
        ar.full_clean()
        ar.save()
        FBV = DeferredValidationTestCase.FIELD_x_BLANK_x_VALID
        for field, blank, valid in FBV:
            self.assertEqual(blank, getattr(ar, field))

    def test_maximum_errors(self):
        ar = Application.objects.create(due_at=self.due_at,
                                        submitted=True,
                                        applicant=self.test_profile)
        with self.assertRaises(ValidationError) as cm:
            ar.full_clean()
            ar.save()
        actual = set(cm.exception.error_dict.keys())
        FBV = DeferredValidationTestCase.FIELD_x_BLANK_x_VALID
        expected = set([fbv[0] for fbv in FBV])
        self.assertEqual(set(), expected - actual)

    def test_minimum_requirements(self):
        st = ScholarshipAward.objects.create(
                name='test scholarship',
                description='A Test Scholarship'
        )
        ar = Application.objects.create(due_at=self.due_at,
                                        submitted=True,
                                        applicant=self.test_profile)
        FBV = DeferredValidationTestCase.FIELD_x_BLANK_x_VALID
        for field, blank, valid in FBV:
            setattr(ar, field, valid)
        ar.scholarshipaward_set.add(st)
        ar.full_clean()
        ar.save()
