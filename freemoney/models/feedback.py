from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import (Manager,
                              Model,
                              CASCADE,
                              ForeignKey,
                              TextField)
import freemoney.models


class FeedbackManager(Manager):
    """Manager class for the Feedback model (see below)"""

    def get_eligible_peers(self):
        """Get a list of all ApplicantProfiles which can be reviewed"""

        users_with_profiles = get_user_model().objects.exclude(
                applicantprofile=None
        ).order_by(
                'last_name', 'first_name'
        ).all()

        return [u.applicantprofile for u in users_with_profiles]

    def custom_validate_for_application(self, application, issues):
        """Perform check on an application (for CustomValidationIssues)"""

        nr_feedbacks = 0
        for feedback in self.filter(application=application).iterator():
            nr_feedbacks += 1
            # TODO: word length tests

        if nr_feedbacks < settings.FREEMONEY_MIN_FEEDBACK_COUNT:
            issues.create(section='feedback', code='min-length')


class Feedback(Model):
    """Represents an applicant's feedback regarding another applicant"""

    application = ForeignKey('Application', on_delete=CASCADE)
    peer = ForeignKey('ApplicantProfile', on_delete=CASCADE)
    feedback = TextField()

    objects = FeedbackManager()
