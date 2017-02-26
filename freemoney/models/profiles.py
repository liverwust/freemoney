from django.conf import settings
from django.db import models


class ApplicantProfile(models.Model):
    """Extra user profile info for a potential applicant's account."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE,
                                primary_key=True)
    must_change_password = models.BooleanField()


class PeerProfile(models.Model):
    """Extra user profile info for a peer who can be reviewed (feedback)."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE,
                                primary_key=True)
    active = models.BooleanField()
    display_name = models.CharField(max_length=255)
