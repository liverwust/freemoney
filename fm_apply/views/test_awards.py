import django.test
from fm_apply import models as fm_models
from fm_apply import views as fm_views
from io import BytesIO
from lxml import etree
import unittest
from unittest.mock import MagicMock, patch


class AwardsPageTestCase(unittest.TestCase):
    """Test applying for awards and general control flow thru this page."""

    def setUp(self):
        self.request_factory = django.test.RequestFactory()

        p1 = patch('fm_apply.views.awards.fm_models.ApplicantResponse')
        self.ApplicantResponseMock = p1.start()
        self.addCleanup(p1.stop)

        p2 = patch('fm_apply.views.awards.fm_models.ScholarshipAwardPrompt')
        self.ScholarshipAwardPromptMock = p2.start()
        scholarship_list = []
        current_pk = 1
        for name in ['test1', 'other', 'supermoney']:
            scholarship_list.append(MagicMock(
                    pk=current_pk,
                    name=name,
                    description='Full description of '+name,
            ))
            current_pk += 1
        self.ScholarshipAwardPromptMock.objects.all = MagicMock(
                return_value=scholarship_list
        )
        self.addCleanup(p2.stop)

    def test_all_awards_for_blank_response(self):
        """For a new response, check all are available but none are chosen."""

        response_mock = MagicMock()
        response_mock.scholarshipawardprompt_set.all.return_value = []
        self.ApplicantResponseMock.objects.get = response_mock

        request = self.request_factory.get('/apply/awards')
        request.session = {'full_response': 42}   # arbitrary response ID
        response = fm_views.wizard_awards(request)

        self.assertEqual(response.status_code, 200)

        ET = etree.parse(BytesIO(response.content), etree.HTMLParser())
        nr_checkboxes = 0
        for checkbox in ET.findall(r".//form//input[@type='checkbox']"):
            nr_checkboxes += 1
        self.assertEqual(3, nr_checkboxes)
