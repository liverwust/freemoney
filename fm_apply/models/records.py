from django.db import models


class FinancialAidRecord(models.Model):
    """An ApplicantResponse record describing sources of financial aid."""

    full_response = models.ForeignKey('ApplicantResponse',
                                      on_delete=models.CASCADE)

    # Response elements
    aid_type = models.CharField(
            'type',
            blank=True,
            max_length=50
    )
    source = models.CharField(
            'source',
            help_text='Full name of the fund, organization, sponsor, etc.',
            blank=True,
            max_length=255
    )
    amount_per_year = models.DecimalField(
            null=True,
            blank=True,
            max_digits=7,
            decimal_places=2
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    def clean(self, force=False):
        """Perform checks which only apply to a submitted form.

        See the ApplicantResponse.clean() documentation.
        """

        errors = {}
        if self.full_response.submitted or force:
            if self.aid_type == '':
                errors['aid_type'] = ('aid type cannot be left blank',
                                      'required')
            if self.source == '':
                errors['source'] = ('source cannot be left blank',
                                     'required')
            if self.amount_per_year == None:
                errors['amount_per_year'] = ('yearly amount is required',
                                             'required')
            if self.start_date == None:
                errors['start_date'] = ('start date is required',
                                        'required')
            elif self.start_date > datetime.date.today():
                errors['start_date'] = ('start date is in the future',
                                        'invalid')
            if self.end_date == None:
                pass   # no problem -- the source is ongoing
            elif self.end_date < datetime.date.today():
                errors['end_date'] = ('end date is in the past',
                                      'invalid')
            elif self.start_date != None and self.end_date < self.start_date:
                errors['end_date'] = ('end date is before start date',
                                      'invalid')

        for field in errors.keys():
            errors[field] = ValidationError(errors[field][0],
                                            code=errors[field][1])
        if len(errors) > 0:
            raise ValidationError(errors)


# TODO: once Financial Records are tested, revive this
#class ActivityRecord(models.Model):
#    """An ApplicantResponse record describing activities & accomplishments."""
#    response = models.ForeignKey('ApplicantResponse',
#                                 on_delete=models.CASCADE)
#    activity_type = models.CharField(max_length=50)
#    description = models.CharField(max_length=255)
#    accomplishments = models.CharField(max_length=255)
#    start_date = models.DateField()
#    end_date = models.DateField()
