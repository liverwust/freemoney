from .validation  import (CustomValidationIssue,
                          CustomValidationIssueSet)
from .semester    import (Semester, SemesterField)
from .activity    import  Activity
from .application import  Application
from .award       import  Award
from .essay       import (Essay, EssayPrompt)
from .feedback    import  PeerFeedback


from django.conf  import settings
import django.db.models as _dmodels


class ApplicantProfile(_dmodels.Model):
    """Extra user profile info for a potential applicant's account"""

    user = _dmodels.OneToOneField(settings.AUTH_USER_MODEL,
                                     on_delete=_dmodels.CASCADE,
                                     primary_key=True)
    current_application = _dmodels.ForeignKey(Application,
                                              on_delete=_dmodels.SET_NULL,
                                              null=True)
    must_change_password = _dmodels.BooleanField(default=False)
