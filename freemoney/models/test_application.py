from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.validators import ValidationError
from django.test import TestCase
from freemoney.models import (Application,
                              ApplicantProfile,
                              ScholarshipAward,
                              PeerFeedback,
                              Semester)


class ApplicationValidationTests(TestCase):
    """Test the validation of Application model fields."""

    def setUp(self):
        self.applicant = ApplicantProfile.objects.create(
                user=get_user_model().objects.create_user(
                        username='test@example.com',
                        password='pass1234'
                ),
                is_first_login=False
        )
        self.application = Application.objects.create(
                applicant=self.applicant,
                application_semester = Semester('SP10')
        )

    def attempt_valid_and_invalid_values(self, attr, valids, invalids):
        consolidated = (list(zip(valids,   [True]  * len(valids))) +
                        list(zip(invalids, [False] * len(invalids))))
        for attempt, is_valid in consolidated:
            try:
                setattr(self.application, attr, attempt)
                self.application.full_clean()
            except ValidationError as exc:
                if is_valid:
                    self.assertNotIn(attr, exc.message_dict)
                else:
                    self.assertIn(attr, exc.message_dict)

    def test_phone_number(self):
        self.attempt_valid_and_invalid_values('phone',
                valids=('609-412-4321', '1 (800) 234 1234'),
                invalids=('not a number', '123456789', '')
        )

    def test_psu_email(self):
        self.attempt_valid_and_invalid_values('psu_email',
                valids=('test@psu.edu'),
                invalids=('test@gmail.com')
        )

    def test_psu_id(self):
        self.attempt_valid_and_invalid_values('psu_id',
                valids=('912345678', '987654321'),
                invalids=('812345678', '12345678', 'NaN', '')
        )

    def test_semester_initiated(self):
        self.attempt_valid_and_invalid_values('semester_initiated',
                valids=(Semester('Fall 2009'), Semester('Spring 2010')),
                invalids=(Semester('Fall 2010'), Semester('SP11'), None)
        )

    def test_semester_graduating(self):
        self.attempt_valid_and_invalid_values('semester_graduating',
                valids=(Semester('Fall 2010'), Semester('Spring 2010')),
                invalids=(Semester('Fall 2009'), Semester('Spring 2009'), None)
        )

    def test_cumulative_gpa(self):
        self.attempt_valid_and_invalid_values('cumulative_gpa',
                valids=(Decimal('0.00'), Decimal('2.05'), Decimal('4.00')),
                invalids=(Decimal('4.01'), Decimal('-0.01'))
        )

    def test_semester_gpa(self):
        self.attempt_valid_and_invalid_values('semester_gpa',
                valids=(Decimal('0.00'), Decimal('2.05'), Decimal('4.00')),
                invalids=(Decimal('4.01'), Decimal('-0.01'))
        )
