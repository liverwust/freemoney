from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import MultipleObjectsReturned
from django.test import TestCase
from freemoney.models import (ApplicantProfile,
                              Application,
                              Semester)


class ApplicantProfileAvailabilityTests(TestCase):
    """Verify that profiles are available, under the correct circumstances"""

    def setUp(self):
        self.new_old_applicant = self._create_applicant(name='Alice',
                                                        is_active=True,
                                                        has_new_app=True,
                                                        has_old_app=True)
        self.old_applicant = self._create_applicant(name='Bob',
                                                    is_active=True,
                                                    has_new_app=False,
                                                    has_old_app=True)

    def _create_applicant(self, name, is_active, has_new_app, has_old_app):
        applicant = ApplicantProfile.objects.create(
                user=get_user_model().objects.create_user(
                        username=name+'@example.com',
                        password=name+'1234',
                        is_active=is_active,
                ),
                must_change_password=False
        )
        if has_new_app:
            new_app = Application.objects.create(
                    applicant=applicant,
                    due_at=settings.FREEMONEY_DUE_DATE
            )
        if has_old_app:
            due_at = settings.FREEMONEY_DUE_DATE - timedelta(weeks=52)
            old_app = Application.objects.create(
                    applicant=applicant,
                    due_at=due_at,
                    submitted=False   # not a perfect test...
            )
        return applicant

    def test_good_current_application(self):
        """Verify that the correct Application is found"""

        self.assertEqual(self.new_old_applicant.current_application,
                         Application.objects.get(
                                due_at=settings.FREEMONEY_DUE_DATE
                         )
        )

    def test_no_current_application(self):
        """Verify that no Application is found, correctly"""

        self.assertEqual(self.old_applicant.current_application, None)

    def test_bad_multiple_applications(self):
        """Verify that multiple applications are detected"""

        multi_applicant = self._create_applicant(name='Charlie',
                                                 is_active=True,
                                                 has_new_app=True,
                                                 has_old_app=False)
        dupe = Application.objects.create(
                applicant=multi_applicant,
                due_at=(settings.FREEMONEY_DUE_DATE + timedelta(days=3))
        )
        with self.assertRaises(MultipleObjectsReturned):
            multi_applicant.current_application

    def test_active_profiles(self):
        """Verify that all appropriate applicants are listed"""

        new_applicant = self._create_applicant(name='Daniel',
                                               is_active=True,
                                               has_new_app=True,
                                               has_old_app=False)

        inactive_applicant = self._create_applicant(name='Eric',
                                                    is_active=False,
                                                    has_new_app=True,
                                                    has_old_app=True)

        found_profiles = ApplicantProfile.objects.active_profiles()
        found_names = []
        for profile in found_profiles:
            found_name = profile.user.username
            found_name = found_name.replace('@example.com', '')
            found_names.append(found_name)
        self.assertSetEqual(set(found_names),
                            set(['Alice', 'Daniel']))
