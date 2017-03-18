from datetime import date, datetime, timezone
from decimal import Decimal
from django.conf import settings
from django.db.models import (Model,
                              CASCADE,
                              DateField,
                              DecimalField,
                              ForeignKey,
                              SlugField,
                              TextField)
from freemoney.models import Semester


class FinancialAid(Model):
    """An Application record describing a source of financial aid."""

    application = ForeignKey('Application', on_delete=CASCADE)
    aid_type = SlugField(blank=True)
    provider = TextField(blank=True)
    end_date = DateField(null=True, blank=True)
    installment_frequency = TextField(blank=True)
    installment_amount = DecimalField(null=True,
                                      blank=True,
                                      max_digits=7,
                                      decimal_places=2)

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

        if (self.aid_type == '' or
            self.provider == '' or
            self.installment_frequency == ''):
            issues.create(section='finaid',
                          field='[records]',
                          subfield=self.pk,
                          code='required')

        issue_invalid_present = False

        if self.installment_amount < Decimal('0.00'):
            issues.create(section='finaid',
                          field='[records]',
                          subfield=self.pk,
                          code='invalid')
            issue_invalid_present = True

        if self.end_date is not None:
            end_semester = Semester(datetime(year=self.end_date.year,
                                             month=self.end_date.month,
                                             day=self.end_date.day,
                                             tzinfo=timezone.utc))
            if end_semester < Semester(settings.FREEMONEY_DUE_DATE):
                if not issue_invalid_present:
                    issues.create(section='finaid',
                                field='[records]',
                                subfield=self.pk,
                                code='invalid')
                    issue_invalid_present = True
