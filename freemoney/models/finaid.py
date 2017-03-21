from django.conf import settings
from django.db.models import (Model,
                              CASCADE,
                              FloatField,
                              ForeignKey,
                              SlugField,
                              TextField)
from freemoney.models import Semester, SemesterField


class FinancialAid(Model):
    """An Application record describing a source of financial aid."""

    application = ForeignKey('Application', on_delete=CASCADE)
    aid_type = SlugField(blank=True)
    provider = TextField(blank=True)
    semester_finished = SemesterField(null=True, blank=True)
    installment_frequency = TextField(blank=True)
    installment_amount = FloatField(null=True, blank=True)

    @property
    def yearly_amount(self):
        if self.installment_frequency == 'yearly':
            return self.installment_amount
        elif self.installment_frequency == 'semesterly':
            return self.installment_amount * 2
        elif self.installment_frequency == 'monthly':
            return self.installment_amount * 12
        elif self.installment_frequency == 'weekly':
            return self.installment_amount * 52
        else:
            raise ValueError('cannot calculate using frequency: ' +
                             self.installment_frequency)

    def custom_validate(self, issues):
        """This is "custom" validation as per Application.custom_validate"""

        if self.aid_type == '':
            issues.create(section='finaid',
                          field='aid_type',
                          subfield=self.pk,
                          code='required')

        if self.provider == '':
            issues.create(section='finaid',
                          field='provider',
                          subfield=self.pk,
                          code='required')

        if self.installment_frequency == '':
            issues.create(section='finaid',
                          field='installment_frequency',
                          subfield=self.pk,
                          code='required')

        if self.installment_amount is None:
            issues.create(section='finaid',
                          field='installment_amount',
                          subfield=self.pk,
                          code='required')
        elif (self.installment_amount < 0.0 or
              self.installment_amount > 200000.0):
            issues.create(section='finaid',
                          field='installment_amount',
                          subfield=self.pk,
                          code='invalid')

        if self.semester_finished is not None:
            if self.semester_finished < Semester(settings.FREEMONEY_DUE_DATE):
                issues.create(section='finaid',
                            field='semester_finished',
                            subfield=self.pk,
                            code='invalid')
