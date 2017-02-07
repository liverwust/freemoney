import datetime
from django.db import models


class VersionedPrompt(models.Model):
    """Generic base class for prompts which might be modified.

    The reason to "version" a prompt (which includes scholarship descriptions)
    is to ensure that an applicant's response can be forever linked with the
    *original* version of the text which he saw. Reworking the text of such a
    prompt could alter the context of the response.
    """
    class Meta:
        abstract = True

    persistent_tag = models.SlugField(blank=True)
    created_at = models.DateTimeField()
    previous_version = models.ForeignKey('self',
                                         null=True,
                                         blank=True,
                                         on_delete=models.SET_NULL)

    def _set_created_at_before_save(self):
        """Call this method from save() before proceeding."""
        # TODO: can this be done without save() duplication?
        if self.created_at == None:
            self.created_at = datetime.datetime.now(datetime.timezone.utc)


class EssayPrompt(VersionedPrompt):
    """The prompt for an essay question."""

    applicantresponse_set = models.ManyToManyField('ApplicantResponse',
                                                   through='EssayResponse')
    prompt = models.TextField()

    def save(self, *args, **kwargs):
        self._set_created_at_before_save()
        super(EssayPrompt, self).save(*args, **kwargs)


class ScholarshipAwardPrompt(VersionedPrompt):
    """Represents a particular scholarship award."""

    applicantresponse_set = models.ManyToManyField('ApplicantResponse')
    name = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self._set_created_at_before_save()
        super(ScholarshipAwardPrompt, self).save(*args, **kwargs)
