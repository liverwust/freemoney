from datetime import datetime, timedelta, timezone
from django import test
from django.urls import reverse
from fm_apply import models as fm_models
from fm_apply import views as fm_views
from io import BytesIO
from lxml import etree


class AwardsPageTestCase(test.TestCase):
    """Test applying for awards and general control flow thru this page."""

    def setUp(self):
        fm_models.ScholarshipAwardPrompt.objects.create(
                persistent_tag='',
                name='Scholarship 1',
                description='Win money for being awesome!'
        )
        fm_models.ScholarshipAwardPrompt.objects.create(
                persistent_tag='',
                name='Scholarship 2',
                description="Don't delay, apply today!"
        )
        fm_models.ScholarshipAwardPrompt.objects.create(
                persistent_tag='',
                name='schp3 333333333333333333333333333333333333333333',
                description='Yep, keep <b>winning</b> monnnnnney & stuff'
        )
        self.response_so_far = fm_models.ApplicantResponse.objects.create(
                due_at=(datetime.now(timezone.utc) + timedelta(weeks=1))
        )
        session = self.client.session
        session['full_response'] = self.response_so_far.pk
        session.save()

    def test_all_awards_for_blank_response(self):
        """For a new response, check all are available but none are chosen."""

        response = self.client.get(reverse('fm_apply:awards'))
        self.assertEqual(response.status_code, 200)

        ET = etree.parse(BytesIO(response.content), etree.HTMLParser())
        nr_checkboxes = 0
        for checkbox in ET.findall(r".//form//input[@type='checkbox']"):
            nr_checkboxes += 1
        self.assertEqual(3, nr_checkboxes)

    def test_select_one_by_one(self):
        """Starting from none, select each available award in turn."""

        checkboxes = {}
        while True:
            page = self.client.get(reverse('fm_apply:awards'))
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
                self.client.post(reverse('fm_apply:awards'), checkboxes)
            else:
                break
        self.assertEqual(len(checkboxes), 3)

    def test_select_deselect_all_at_once(self):
        """Starting from none, select all awards, then deselect all."""

        page = self.client.get(reverse('fm_apply:awards'))
        ET = etree.parse(BytesIO(page.content), etree.HTMLParser())
        checkboxes = {}
        for element in ET.findall(r".//form//input[@type='checkbox']"):
            checkboxes[element.get('name')] = 'on'

        # select all checkboxes
        self.client.post(reverse('fm_apply:awards'), checkboxes)

        page = self.client.get(reverse('fm_apply:awards'))
        ET = etree.parse(BytesIO(page.content), etree.HTMLParser())
        for element in ET.findall(r".//form//input[@type='checkbox']"):
            self.assertIn(element.get('name'), checkboxes)
            self.assertEqual(element.get('value'), 'on')

        # deselect all checkboxes
        self.client.post(reverse('fm_apply:awards'))

        page = self.client.get(reverse('fm_apply:awards'))
        ET = etree.parse(BytesIO(page.content), etree.HTMLParser())
        for element in ET.findall(r".//form//input[@type='checkbox']"):
            self.assertEqual(element.get('value', None), None)
