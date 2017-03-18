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

        profiles = freemoney.models.ApplicantProfile.objects.active_profiles()

        # Convert "John Smith" to "SmithJohn" and then add padding so that the
        # last name is as long as the longest last name, "Smith     John"
        # (this allows for direct key-based comparison between names)
        max_lastname_len = max([len(p.user.last_name) for p in profiles])
        def _parameterized_keyfunc(p):
            return (p.user.last_name +
                    " " * (max_lastname_len - len(p.user.last_name)) +
                    p.user.first_name)

        return sorted(profiles, key=_parameterized_keyfunc)

    def custom_validate_for_application(self, application, issues):
        """Perform check on an application (for CustomValidationIssues)"""

        nr_feedbacks = 0
        for feedback in self.filter(application=application).iterator():
            if feedback.peer != application.applicant:
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
