from datetime import datetime, timezone
from django.contrib.auth import get_user_model
from django.test import TestCase
from freemoney.models import (ApplicantProfile,
                              Application,
                              Award,
                              CustomValidationIssueSet,
                              Essay,
                              EssayPrompt,
                              Semester)


class EssayPromptTests(TestCase):
    """Test the validation of Essay responses within an Application"""

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

    # TODO: TESTS!!!!!!!!
