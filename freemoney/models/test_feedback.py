from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from freemoney.models import (ApplicantProfile,
                              Application,
                              CustomValidationIssueSet,
                              Feedback)


class FeedbackApplicationTests(TestCase):
    """Test the validation of Feedback within an Application"""

    # TODO: word counts

    def test_minimum_feedback_count(self):
        profiles = []
        for i in range(1234, 1234 + 5):
            profile = ApplicantProfile.objects.create(
                    user=get_user_model().objects.create_user(
                            username='test{}@example.com'.format(i),
                            password='pass{}'.format(i),
                            first_name='Test',
                            last_name=str(i)
                    ),
                    must_change_password=False
            )
            Application.objects.create(
                    applicant=profile,
                    due_at=settings.FREEMONEY_DUE_DATE
            )
            profiles.append(profile)
        my_profile = profiles[-1]

        for i in range(3):
            feedback = Feedback.objects.create(
                    application=my_profile.current_application,
                    peer=profiles[i],
                    feedback='Testing 1, 2, 3...'
            )
            profiles[i] = (profiles[i], feedback)
        issues = CustomValidationIssueSet()
        my_profile.current_application.custom_validate(issues)
        self.assertEqual(list(issues.search(
                section='feedback',
                field=CustomValidationIssueSet.GLOBAL,
                code='min-length'
        )), [])

        profiles[2][1].delete()
        issues = CustomValidationIssueSet()
        my_profile.current_application.custom_validate(issues)
        self.assertNotEqual(list(issues.search(
                section='feedback',
                field=CustomValidationIssueSet.GLOBAL,
                code='min-length'
        )), [])


class FeedbackAvailabilityTest(TestCase):
    """Verify that Awards are available, and under the correct circumstances"""

    def test_sort_by_last_first(self):
        """Verify that eligible peers are properly sorted"""

        names = {1234: ('John', 'Smith'),
                 1235: ('James', 'Smith'),
                 1236: ('John', 'Smithington'),
                 1237: ('Greg', 'Frenchington'),
                 1238: ('John', 'French')}

        for i in range(1234, 1234 + 5):
            profile = ApplicantProfile.objects.create(
                    user=get_user_model().objects.create_user(
                            username='test{}@example.com'.format(i),
                            password='pass{}'.format(i),
                            first_name=names[i][0],
                            last_name=names[i][1]
                    ),
                    must_change_password=False
            )
            Application.objects.create(
                    applicant=profile,
                    due_at=settings.FREEMONEY_DUE_DATE
            )

        names = []
        for profile in Feedback.objects.get_eligible_peers():
            names.append((profile.user.first_name, profile.user.last_name))

        self.assertListEqual(names, [('John', 'French'),
                                     ('Greg', 'Frenchington'),
                                     ('James', 'Smith'),
                                     ('John', 'Smith'),
                                     ('John', 'Smithington')])
