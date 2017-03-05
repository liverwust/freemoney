from .validation  import (CustomValidationIssue,
                          CustomValidationIssueSet)
from .semester    import (Semester, SemesterField)
from .activity    import  Activity
from .application import  Application
from .award       import (ScholarshipAward, ScholarshipAwardPrompt)
from .essay       import (Essay, EssayPrompt)
from .feedback    import  PeerFeedback


from django.conf  import settings
import django.db.models as _ddb_models


class ApplicantProfile(_ddb_models.Model):
    """Extra user profile info for a potential applicant's account"""

    user = _ddb_models.OneToOneField(settings.AUTH_USER_MODEL,
                                     on_delete=_ddb_models.CASCADE,
                                     primary_key=True)
    must_change_password = _ddb_models.BooleanField(default=False)
