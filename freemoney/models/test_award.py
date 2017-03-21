import contextlib
from datetime import datetime, timezone
from django.contrib.auth import get_user_model
from django.test import TestCase
from freemoney.models import (ApplicantProfile,
                              Application,
                              CustomValidationIssueSet,
                              Award,
                              Semester)


class AwardApplicationTests(TestCase):
    """Test the validation of Awards within an Application"""

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

    def test_differing_semester_awards(self):
        fall_awards = Award.objects.for_semester(Semester('FA10'))
        spring_awards = Award.objects.for_semester(Semester('SP17'))
        self.assertNotEqual(set(fall_awards), set(spring_awards))

    def test_too_few_awards(self):
        """Verify that at least one award must be selected"""

        issues = CustomValidationIssueSet()
        self.application.custom_validate(issues)
        self.assertNotEqual(list(issues.search(section='award',
                                               code='min-length')), [])

        excellence = Award.objects.latest_version_of('excellence')
        self.application.award_set.add(excellence)
        issues = CustomValidationIssueSet()
        self.application.custom_validate(issues)
        self.assertEqual(list(issues.search(section='award')), [])

        self.application.award_set.clear()
        issues = CustomValidationIssueSet()
        self.application.custom_validate(issues)
        self.assertNotEqual(list(issues.search(section='award',
                                               code='min-length')), [])

    def test_non_semester_award(self):
        """Verify error if a Spring award is selected in the Fall"""

        excellence = Award.objects.latest_version_of('excellence')
        self.application.award_set.add(excellence)
        issues = CustomValidationIssueSet()
        self.application.custom_validate(issues)
        self.assertEqual(list(issues.search(section='award')), [])

        ambassador = Award.objects.latest_version_of('ambassador')
        self.application.award_set.add(ambassador)
        issues = CustomValidationIssueSet()
        self.application.custom_validate(issues)
        self.assertNotEqual(list(issues.search(section='award',
                                               code='invalid')), [])

    def test_endowment_senior_limitation(self):
        """Ensure that a graduating senior cannot select endowment awards"""

        excellence = Award.objects.latest_version_of('excellence')

        self.application.semester_graduating = Semester('FA16')
        self.application.award_set.add(excellence)
        issues = CustomValidationIssueSet()
        self.application.custom_validate(issues)
        self.assertNotEqual(list(issues.search(section='basicinfo',
                                                field='semester_graduating',
                                                code='prohibited')), [])

    def test_major_restrictions(self):
        """Ensure that only certain majors can apply to restricted awards"""

        joe_conway = Award.objects.latest_version_of('joe_conway')
        giff_albright = Award.objects.latest_version_of('giff_albright')

        self.application.award_set.set([giff_albright])
        self.application.major = 'Electrical Engineering'
        self.application.full_clean()
        self.application.save()
        issues = CustomValidationIssueSet()
        self.application.custom_validate(issues)
        self.assertNotEqual(list(issues.search(section='basicinfo',
                                               field='major',
                                               code='prohibited')), [])

        self.application.award_set.set([giff_albright])
        self.application.major = 'Architectural Engineering'
        self.application.full_clean()
        self.application.save()
        issues = CustomValidationIssueSet()
        self.application.custom_validate(issues)
        self.assertEqual(list(issues.search(section='basicinfo',
                                            field='major',
                                            code='prohibited')), [])

        self.application.award_set.set([joe_conway])
        self.application.major = 'Electrical Engineering'
        self.application.full_clean()
        self.application.save()
        issues = CustomValidationIssueSet()
        self.application.custom_validate(issues)
        self.assertNotEqual(list(issues.search(section='basicinfo',
                                               field='major',
                                               code='prohibited')), [])

        self.application.award_set.set([joe_conway])
        self.application.emch_minor = True
        self.application.full_clean()
        self.application.save()
        issues = CustomValidationIssueSet()
        self.application.custom_validate(issues)
        self.assertEqual(list(issues.search(section='basicinfo',
                                            field='major',
                                            code='prohibited')), [])

        self.application.award_set.set([joe_conway])
        self.application.major = 'Engineering Science'
        self.application.emch_minor = False
        self.application.full_clean()
        self.application.save()
        issues = CustomValidationIssueSet()
        self.application.custom_validate(issues)
        self.assertEqual(list(issues.search(section='basicinfo',
                                            field='major',
                                            code='prohibited')), [])

class AwardAvailabilityTest(TestCase):
    """Verify that Awards are available, and under the correct circumstances"""

    def setUp(self):
        self.old = Award.objects.create(identifier='test',
                                        name='Test Award',
                                        description='Text for oldest version',
                                        previous_version=None)
        self.mid = Award.objects.create(identifier='test',
                                        name='Test Award',
                                        description='Text for middle version',
                                        previous_version=self.old)
        self.new = Award.objects.create(identifier='test',
                                        name='Test Award',
                                        description='Text for newest version',
                                        previous_version=self.mid)

    def test_latest_award_nominal(self):
        """Check that the latest version of an award is returned"""
        self.assertEqual(self.new,
                         Award.objects.latest_version_of('test'))

    def test_latest_award_with_cycle(self):
        """Verify graceful handling of an infinite foreign key loop"""

        self.old.previous_version = self.new
        self.old.full_clean()
        self.old.save()
        with self.assertRaises(ValueError):
            Award.objects.latest_version_of('test')

    def test_latest_award_with_split(self):
        """Verify graceful handling of a *split* or *branched* award"""

        self.mid.previous_version = None
        self.mid.full_clean()
        self.mid.save()
        with self.assertRaises(ValueError):
            Award.objects.latest_version_of('test')

    def test_latest_award_with_selfcycles(self):
        """The worst case: each award points to itself, independently"""

        for award in Award.objects.filter(identifier='test'):
            award.previous_version = award
            award.save()
        with self.assertRaises(ValueError):
            Award.objects.latest_version_of('test')
