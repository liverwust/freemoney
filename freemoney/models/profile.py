from django.conf  import settings
from django.db.models import(Model,
                             Manager,
                             CASCADE,
                             BooleanField,
                             ForeignKey,
                             OneToOneField)
from freemoney.models import (Application,
                              Semester)


class ApplicantProfileManager(Manager):
    def active_profiles(self):
        """Get all active ApplicantProfiles with a current Application"""

        filtered_profiles = []
        for profile in self.iterator():
            if profile.user.is_active:
                if profile.current_application is not None:
                    filtered_profiles.append(profile)
        return filtered_profiles

class ApplicantProfile(Model):
    """Extra user profile info for a potential applicant's account"""

    user = OneToOneField(settings.AUTH_USER_MODEL,
                         on_delete=CASCADE,
                         primary_key=True)
    must_change_password = BooleanField(default=False)

    objects = ApplicantProfileManager()

    @property
    def current_application(self):
        candidate_applications = []
        for application in self.application_set.iterator():
            if (Semester(application.due_at) ==
                Semester(settings.FREEMONEY_DUE_DATE)):
                candidate_applications.append(application)
        if len(candidate_applications) == 0:
            return None
        elif len(candidate_applications) == 1:
            return candidate_applications.pop()
        else:
            raise Application.MultipleObjectsReturned()
