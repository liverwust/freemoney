from datetime import datetime, timedelta, timezone
from django import test
from django.contrib.auth import get_user_model
from django.urls import reverse
from freemoney.models import Application, ApplicantProfile, ScholarshipAward
from io import BytesIO
from lxml import etree


class AwardsPageTestCase(test.TestCase):
    """Test applying for awards and general control flow thru this page."""

    def setUp(self):
        self.test_user = get_user_model().objects.create_user(
                username='test@example.com',
                password='pass1234'
        )
        self.test_profile = ApplicantProfile.objects.create(
                user=self.test_user,
                must_change_password=False
        )
        self.client.login(username='test@example.com', password='pass1234')
        ScholarshipAward.objects.create(
                persistent_tag='',
                name='Scholarship 1',
                description='Win money for being awesome!'
        )
        ScholarshipAward.objects.create(
                persistent_tag='',
                name='Scholarship 2',
                description="Don't delay, apply today!"
        )
        ScholarshipAward.objects.create(
                persistent_tag='',
                name='schp3 333333333333333333333333333333333333333333',
                description='Yep, keep <b>winning</b> monnnnnney & stuff'
        )
        self.application_so_far = Application.objects.create(
                due_at=(datetime.now(timezone.utc) + timedelta(weeks=1)),
                applicant=self.test_profile
        )
        session = self.client.session
        session['application'] = self.application_so_far.pk
        session.save()

    def test_all_awards_for_blank_application(self):
        """For new application, check all are available but none are chosen."""

        response = self.client.get(reverse('freemoney:awards'))
        self.assertEqual(response.status_code, 200)

        ET = etree.parse(BytesIO(response.content), etree.HTMLParser())
        nr_checkboxes = 0
        for checkbox in ET.findall(r".//form//input[@type='checkbox']"):
            nr_checkboxes += 1
        self.assertEqual(3, nr_checkboxes)

    def test_select_one_by_one(self):
        """Starting from none, select each available award in turn."""

        checkboxes = {'submit-type': 'next'}
        baseline_len = len(checkboxes)
        while True:
            page = self.client.get(reverse('freemoney:awards'))
            ET = etree.parse(BytesIO(page.content), etree.HTMLParser())
            found_new_one = False
            for element in ET.findall(r".//form//input[@type='checkbox']"):
                name, value = element.get('name'), element.get('value', None)
                if name in checkboxes:
                    self.assertEqual(value, 'on')
                else:
                    if found_new_one:
                        self.assertEqual(value, None)
                    else:
                        checkboxes[name] = 'on'
                        found_new_one = True
            if found_new_one:
                self.client.post(reverse('freemoney:awards'), checkboxes)
            else:
                break
        self.assertEqual(len(checkboxes), 3 + baseline_len)

    def test_select_deselect_all_at_once(self):
        """Starting from none, select all awards, then deselect all."""

        page = self.client.get(reverse('freemoney:awards'))
        ET = etree.parse(BytesIO(page.content), etree.HTMLParser())
        checkboxes = {'submit-type': 'next'}
        for element in ET.findall(r".//form//input[@type='checkbox']"):
            checkboxes[element.get('name')] = 'on'

        # select all checkboxes
        self.client.post(reverse('freemoney:awards'), checkboxes)

        page = self.client.get(reverse('freemoney:awards'))
        ET = etree.parse(BytesIO(page.content), etree.HTMLParser())
        for element in ET.findall(r".//form//input[@type='checkbox']"):
            self.assertIn(element.get('name'), checkboxes)
            self.assertEqual(element.get('value'), 'on')

        # deselect all checkboxes
        no_checkboxes = {'submit-type': 'next'}
        self.client.post(reverse('freemoney:awards'), no_checkboxes)

        page = self.client.get(reverse('freemoney:awards'))
        ET = etree.parse(BytesIO(page.content), etree.HTMLParser())
        for element in ET.findall(r".//form//input[@type='checkbox']"):
            self.assertEqual(element.get('value', None), None)
