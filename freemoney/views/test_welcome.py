from datetime import datetime, timedelta, timezone
from django import test
from django.contrib.auth import get_user_model
from django.urls import reverse
from freemoney.models import Application, ApplicantProfile
from io import BytesIO
from lxml import etree


class CommonWizardViewTestCase(test.TestCase):
    """Test the basic functionality of a WizardView (mostly thru Welcome)"""

    def setUp(self):
        self.test_user = get_user_model().objects.create_user(
                username='test@example.com',
                password='pass1234'
        )
        self.test_profile = ApplicantProfile.objects.create(
                user=self.test_user,
                must_change_password=False
        )
        self.client.login(username='test@example.com', password='pass1234')

    def test_duplicate_semester_applications(self):
        """Ensure that a user can only have one active application."""
        # TODO: need to be able to set this from the test
        cycle_due_date = datetime(year=2017, month=3, day=17, 
                                  hour=23, minute=52, second=51,
                                  tzinfo=timezone.utc)
        self.client.get(reverse('freemoney:welcome'))
        dupe_application = Application.objects.create(
                due_at=cycle_due_date,
                applicant=self.test_profile
        )
        # TODO: should NOT check for an exception, but an error page!
        #response = self.client.get(reverse('freemoney:welcome'))
        with self.assertRaises(Exception):
            self.client.get(reverse('freemoney:welcome'))

    def test_multi_user_semester_apps(self):
        """*Different* users must be able to have apps in the same semester"""
        # TODO: need to be able to set this from the test
        cycle_due_date = datetime(year=2017, month=3, day=17, 
                                  hour=23, minute=52, second=51,
                                  tzinfo=timezone.utc)
        other_user = get_user_model().objects.create_user(
                username='test2@example.com',
                password='pass2345'
        )
        other_profile = ApplicantProfile.objects.create(
                user=other_user,
                must_change_password=False
        )
        other_application = Application.objects.create(
                due_at=cycle_due_date,
                applicant=other_profile
        )
        response = self.client.get(reverse('freemoney:welcome'))
        self.assertIn('application', self.client.session)
        self.assertTemplateUsed(response, 'welcome.html')


class CommonWizardViewTestCaseNoProfile(test.TestCase):
    """Similar to the previous TestCase, but without an ApplicantProfile."""

    def setUp(self):
        test_user = get_user_model().objects.create_user(
                username='test@example.com',
                password='pass1234'
        )
        # no ApplicantProfile
        self.client.login(username='test@example.com', password='pass1234')

    def test_having_applicant_profile(self):
        """Verify that auth'ing isn't enough -- need an ApplicantProfile"""
        response = self.client.get(reverse('freemoney:welcome'))
        self.assertTemplateNotUsed(response, 'welcome.html')
