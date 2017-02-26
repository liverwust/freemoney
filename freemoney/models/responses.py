from django.contrib import auth
from django.db import models


class AdditionalRemark(models.Model):
    """Represents additional info provided by the applicant.

    There are a few text fields where an applicant can enter additional
    remarks. They are all optional and somewhat "out-of-band," so they are
    stored here rather than directly in the Application.
    """

    application = models.ForeignKey('Application', on_delete=models.CASCADE)
    remark_type = models.SlugField()
    remark_content = models.TextField('additional remarks')


class Essay(models.Model):
    """An Application record containing an essay."""

    application = models.ForeignKey('Application', on_delete=models.CASCADE)
    prompt = models.ForeignKey('EssayPrompt', on_delete=models.CASCADE)
    text = models.TextField()


class PeerFeedback(models.Model):
    """Represents an applicant's feedback regarding another brother."""

    application = models.ForeignKey('Application', on_delete=models.CASCADE)
    peer = models.ForeignKey('PeerProfile', on_delete=models.CASCADE)
    feedback = models.TextField()
