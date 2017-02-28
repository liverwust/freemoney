import contextlib
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from freemoney.models import (ApplicantProfile,
                              Application,
                              ScholarshipAward,
                              ScholarshipAwardPicker,
                              ScholarshipAwardPrompt,
                              Semester)

class ScholarshipAwardPickerTestCase(TestCase):
    """Verify that the rules in the ScholarshipAwardPicker are enforced"""

    def setUp(self):
        self.fall_applicant = ApplicantProfile.objects.create(
                user=get_user_model().objects.create_user(
                        username='fall@example.com',
                        password='pass1234'
                ),
                is_first_login=False
        )
        self.fall_application = Application.objects.create(
                applicant=self.fall_applicant,
                application_semester = Semester('FA10')
        )
        self.spring_applicant = ApplicantProfile.objects.create(
                user=get_user_model().objects.create_user(
                        username='spring@example.com',
                        password='pass1234'
                ),
                is_first_login=False
        )
        self.spring_application = Application.objects.create(
                applicant=self.spring_applicant,
                application_semester = Semester('SP10')
        )
        for award in set(['ean_hong', 'ambassador', 'giff_albright',
                          'joe_conway', 'dan_summers', 'navy_marine',
                          'excellence', 'pledge']):
            ScholarshipAwardPrompt.objects.create(
                    identifier=award,
                    name='{} Name'.format(award),
                    description = '{} Description'.format(award)
            )

    @contextlib.contextmanager
    def assertRaisesValidationCode(self, expected_code):
        with self.assertRaises(ValidationError) as cm:
            yield
        relevant_errors = []
        for error in cm.exception.messages:
            if isinstance(error, ValidationError):
                if error.code == expected_code:
                    relevant_errors.append(error)
        self.assertNotEqual([], relevant_errors)

    def test_populate(self):
        """Pursue the possibility that the Picker doesn't populate properly"""

        fall_picker = ScholarshipAwardPicker.objects.create_and_populate(
                application=self.fall_application
        )
        expected_fall_awards = set(['ean_hong', 'excellence', 'pledge'])
        for fall_award in fall_picker.scholarshipaward_set.iterator():
            self.assertIn(fall_award.identifier, expected_fall_awards)
            expected_fall_awards.remove(fall_award.identifier)
            matching_prompt = ScholarshipAwardPrompt.objects.get(
                    identifier=fall_award.identifier
            )
            self.assertEqual(matching_prompt.name, fall_award.name)
            self.assertEqual(matching_prompt.description,
                             fall_award.description)
            self.assertEqual(False, fall_award.chosen)

        spring_picker = ScholarshipAwardPicker.objects.create_and_populate(
                application=self.spring_application
        )
        expected_spring_awards = set(['ambassador', 'giff_albright',
                                      'joe_conway', 'dan_summers',
                                      'navy_marine']) | expected_fall_awards
        for spring_award in spring_picker.scholarshipaward_set.iterator():
            self.assertIn(spring_award.identifier, expected_spring_awards)
            expected_spring_awards.remove(spring_award.identifier)
            matching_prompt = ScholarshipAwardPrompt.objects.get(
                    identifier=spring_award.identifier
            )
            self.assertEqual(matching_prompt.name, spring_award.name)
            self.assertEqual(matching_prompt.description,
                             spring_award.description)
            self.assertEqual(False, spring_award.chosen)

    def test_field_manipulation(self):
        """Verify that a few types of field manipulation are detected.

        This is NOT a security-critical test! The user couldn't introduce
        anything into these fields (e.g., via a webform) that could cause
        trouble. I'm merely checking for logic errors.
        """

        picker = ScholarshipAwardPicker.objects.create_and_populate(
                application=self.spring_application
        )
        for award in picker.scholarshipaward_set.iterator():
            award.chosen = True
            award.save()

        false_award = ScholarshipAward.objects.create(
                picker=picker,
                position=99,
                identifier='false',
                name='false Name',
                description='false Description',
                chosen=False
        )
        with self.assertRaisesValidationCode('award:invalid'):
            picker.full_clean()
        false_award.delete()

        try:
            picker.full_clean()
        except ValidationError as exc:
            for error in exc.messages:
                self.assertNotIn('award', error.code)

        picker.scholarshipaward_set.first().delete()
        with self.assertRaisesValidationCode('award:required'):
            picker.full_clean()

        picker.scholarshipaward_set.delete()
        with self.assertRaisesValidationCode('award:min_length'):
            picker.full_clean()

    def test_endowment_senior_limitation(self):
        """Ensure that a graduating senior cannot select endowment awards"""

        full_set = set(['ean_hong', 'ambassador', 'giff_albright',
                        'joe_conway', 'dan_summers', 'navy_marine',
                        'excellence', 'pledge'])
        endowment_set = full_set - set(['ean_hong'])

        self.fall_application.semester_graduating = Semester('FA10')
        fall_picker = ScholarshipAwardPicker.objects.create_and_populate(
                application=self.fall_application
        )
        self.spring_application.semester_graduating = Semester('SP10')
        spring_picker = ScholarshipAwardPicker.objects.create_and_populate(
                application=self.spring_application
        )

        @contextlib.contextmanager
        def _process_picker(picker, identifier_set):
            for identifier in identifier_set:
                try:
                    award = picker.scholarshipaward_set.get(
                            identifier=identifier
                    )
                    yield award
                except ScholarshipAward.DoesNotExist:
                    yield None

        with _process_picker(fall_picker, full_set - endowment_set) as award:
            if award != None:
                award.chosen = True
                award.save()
        with _process_picker(spring_picker, full_set - endowment_set) as award:
            if award != None:
                award.chosen = True
                award.save()
        try:
            fall_picker.full_clean()
        except ValidationError as exc:
            for error in exc.messages:
                if isinstance(error, ValidationError):
                    self.assertNotIn('award', error.code)
        try:
            spring_picker.full_clean()
        except ValidationError as exc:
            for error in exc.messages:
                if isinstance(error, ValidationError):
                    self.assertNotIn('award', error.code)

        for identifier in endowment_set:
            with _process_picker(fall_picker, set([identifier])) as award:
                if award != None:
                    award.chosen = True
                    award.save()
                    with self.raisesValidationCode('award:senior_rule'):
                        fall_picker.full_clean()
                    award.chosen = False
                    award.save()
            with _process_picker(spring_picker, set([identifier])) as award:
                if award != None:
                    award.chosen = True
                    award.save()
                    with self.raisesValidationCode('award:senior_rule'):
                        spring_picker.full_clean()
                    award.chosen = False
                    award.save()
