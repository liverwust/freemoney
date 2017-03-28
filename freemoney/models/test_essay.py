from datetime import datetime, timezone
from django.contrib.auth import get_user_model
from django.test import TestCase
from freemoney.models import (ApplicantProfile,
                              Application,
                              Award,
                              CustomValidationIssueSet,
                              Essay,
                              EssayPrompt,
                              Semester)


class EssayPromptTests(TestCase):
    """Test the validation of Essay responses within an Application"""

    def setUp(self):
        self.applicant = ApplicantProfile.objects.create(
                user=get_user_model().objects.create_user(
                        username='test1234@example.com',
                        password='pass1234'
                ),
                must_change_password=False
        )
        self.application = Application.objects.create(
                applicant=self.applicant,
                due_at = datetime(2016, 11, 15, tzinfo=timezone.utc)
        )

    def test_max_length(self):
        """Verify that the word count is enforced"""
        prompt = EssayPrompt.objects.create(
                identifier='test',
                prompt='This is a test!',
                word_limit=6,
                previous_version=None
        )
        essay = Essay.objects.create(
                application=self.application,
                prompt=prompt,
                response = """lorem ipsum!   facto blargson

                test text"""
        )

        issues = CustomValidationIssueSet()
        self.application.custom_validate(issues)
        found_issues = issues.search(section='essay',
                                     code='max-length')
        self.assertEqual(len(found_issues), 0)

        # Only one more word is needed to meet the advertised limit, but the
        # code is generous and makes this a "soft" limit; add several more
        # words to test the "hard" limit
        essay.response += ' anotherword!' * 6
        essay.full_clean()
        essay.save()
        self.application.custom_validate(issues)
        found_issues = issues.search(section='essay',
                                     code='max-length')
        self.assertEqual(len(found_issues), 1)
        first_iter = iter(found_issues)
        self.assertNotEqual(next(first_iter).subfield, None)


class EssayPromptAvailabilityTests(TestCase):
    """Verify that EssayPrompts are available under specific circumstances"""

    def setUp(self):
        self.old = EssayPrompt.objects.create(
                identifier='test',
                prompt='This is a test!',
                word_limit=500,
                previous_version=None
        )
        self.mid = EssayPrompt.objects.create(
                identifier='test',
                prompt='This is a newer test!',
                word_limit=500,
                previous_version=self.old
        )
        self.new = EssayPrompt.objects.create(
                identifier='test',
                prompt='This is the newest test!',
                word_limit=500,
                previous_version=self.mid
        )

    def test_latest_essay_prompt_nominal(self):
        """Check that the latest version of an essay prompt is returned"""
        self.assertEqual(self.new,
                         EssayPrompt.objects.latest_version_of('test'))

    def test_latest_essay_prompt_with_cycle(self):
        """Verify graceful handling of an infinite foreign key loop"""

        self.old.previous_version = self.new
        self.old.full_clean()
        self.old.save()
        with self.assertRaises(ValueError):
            EssayPrompt.objects.latest_version_of('test')

    def test_latest_essay_prompt_with_split(self):
        """Verify graceful handling of a *split* or *branched* prompt"""

        self.mid.previous_version = None
        self.mid.full_clean()
        self.mid.save()
        with self.assertRaises(ValueError):
            EssayPrompt.objects.latest_version_of('test')

    def test_latest_essay_prompt_with_selfcycles(self):
        """The worst case: each prompt points to itself, independently"""

        for essay in EssayPrompt.objects.filter(identifier='test'):
            essay.previous_version = essay
            essay.save()
        with self.assertRaises(ValueError):
            EssayPrompt.objects.latest_version_of('test')
