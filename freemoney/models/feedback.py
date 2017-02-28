from django.db.models import Manager, Model, ForeignKey, TextField, CASCADE


class PeerFeedbackManager(Manager):
    pass

class PeerFeedback(Model):
    """Represents an applicant's feedback regarding another applicant"""

    application = ForeignKey('Application',
                                         on_delete=CASCADE)
    peer = ForeignKey('ApplicantProfile',
                                  on_delete=CASCADE)
    feedback = TextField(
            help_text='Is he compatible with our principles? Other brothers?'
    )
