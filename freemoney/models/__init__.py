from django.conf import settings
#TODO: revive Activity
#from .activity    import Activity
from .semester    import  Semester, SemesterModelField
from .application import  Application
from .award       import (ScholarshipAward,
                          ScholarshipAwardPicker,
                          ScholarshipAwardPrompt)
#from .essay       import Essay, EssayPicker


import django.db.models as _ddb_models


# The models below are "simple" in that they don't contain complex logic


class ApplicantProfile(_ddb_models.Model):
    """Extra user profile info for a potential applicant's account"""

    user = _ddb_models.OneToOneField(settings.AUTH_USER_MODEL,
                                     on_delete=_ddb_models.CASCADE,
                                     primary_key=True)
    is_first_login = _ddb_models.BooleanField(
            help_text='Should this user be asked to change his password?'
    )


class PeerFeedback(_ddb_models.Model):
    """Represents an applicant's feedback regarding another applicant"""

    application = _ddb_models.ForeignKey(Application,
                                         on_delete=_ddb_models.CASCADE)
    peer = _ddb_models.ForeignKey(ApplicantProfile,
                                  on_delete=_ddb_models.CASCADE)
    feedback = _ddb_models.TextField(
            help_text='Is he compatible with our principles? Other brothers?'
    )
