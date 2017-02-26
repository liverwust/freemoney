from datetime import datetime, timedelta, timezone
from django import test
from django.contrib.auth import get_user_model
from django.urls import reverse
from freemoney.models import (Application,
                              ApplicantProfile,
                              PeerProfile,
                              PeerFeedback,
                              ScholarshipAward)
from freemoney import utils
from io import BytesIO
from lxml import etree
import re


class TestPeerFeedbackPage(test.TestCase):
    """Verify basic functionality of the feedback page."""

    def setUp(self):
        self.users = {}
        for i in list('abcdex'):
            self.users[i] = {
                    'auth': get_user_model().objects.create_user(
                            username='test{}@example.com'.format(i),
                            password='pass1234'
                    )
            }
            self.users[i]['app_profile'] = ApplicantProfile.objects.create(
                    user=self.users[i]['auth'],
                    must_change_password=False
            )
            self.users[i]['peer_profile'] = PeerProfile.objects.create(
                    user=self.users[i]['auth'],
                    active=True,
                    display_name="Test User {}".format(i)
            )
        self.users['x']['peer_profile'].active = False
        self.users['x']['peer_profile'].full_clean()
        self.users['x']['peer_profile'].save()
        award = ScholarshipAward.objects.create(
                persistent_tag='',
                name='Scholarship 1',
                description='Win money for being awesome!'
        )
        self.application_so_far = Application.objects.create(
                due_at=(datetime.now(timezone.utc) + timedelta(weeks=1)),
                applicant=self.users['a']['app_profile']
        )
        self.application_so_far.scholarshipaward_set.set([award])
        self.application_so_far.full_clean()
        self.application_so_far.save()
        self.client.login(username='testa@example.com', password='pass1234')

    def test_list_correct_peers(self):
        """List all peers other than self and inactive."""
        page = self.client.get(reverse('freemoney:feedback'))
        ET = etree.parse(BytesIO(page.content), etree.HTMLParser())
        nr_peers = 0
        peer_ids = set()
        for element in ET.findall(r".//form//input[@type='hidden']"):
            if 'peer_id' in element.get('name'):
                peer_ids.add(int(element.get('value')))
                nr_peers += 1
        self.assertEqual(nr_peers, len(peer_ids))
        peer_ids.remove(self.users['b']['peer_profile'].pk)
        peer_ids.remove(self.users['c']['peer_profile'].pk)
        peer_ids.remove(self.users['d']['peer_profile'].pk)
        peer_ids.remove(self.users['e']['peer_profile'].pk)
        self.assertEqual(set(), peer_ids)

    def test_three_feedback_submissions(self):
        """Submit feedback for all peers and make sure it appears."""
        feedbacks = {
                'b': "He had a lot to say.",
                'c': "He had a lot of nothin' to say.",
                'd': "We'll miss him.",
        }

        page = self.client.get(reverse('freemoney:feedback'))
        ppp_result = self._parse_and_prepare_for_postback(page, feedbacks)
        feedbacks_by_user_i, postdata = ppp_result
        for i in feedbacks_by_user_i.keys():
            self.assertHTMLEqual(feedbacks_by_user_i[i], "")
        self.client.post(reverse('freemoney:feedback'), postdata)

        page = self.client.get(reverse('freemoney:feedback'))
        ppp_result = self._parse_and_prepare_for_postback(page)
        feedbacks_by_user_i, _ = ppp_result
        for i in feedbacks.keys():
            self.assertHTMLEqual(feedbacks_by_user_i[i], feedbacks[i])
        self.assertHTMLEqual(feedbacks_by_user_i['e'], "")

    def test_one_additional_feedback_submission(self):
        """Given that three feedbacks are already in, submit one more."""
        feedbacks = {
                'b': "He had a lot to say.",
                'c': "He had a lot of nothin' to say.",
                'd': "We'll miss him.",
                'e': "We're gonna miss him."
        }
        for i in feedbacks.keys():
            if i != 'e':
                PeerFeedback.objects.create(
                        peer=self.users[i]['peer_profile'],
                        application=self.application_so_far,
                        feedback=feedbacks[i]
                )

        page = self.client.get(reverse('freemoney:feedback'))
        ppp_result = self._parse_and_prepare_for_postback(page, feedbacks)
        feedbacks_by_user_i, postdata = ppp_result
        for i in feedbacks.keys():
            if i == 'e':
                self.assertHTMLEqual(feedbacks_by_user_i[i], "")
            else:
                self.assertHTMLEqual(feedbacks_by_user_i[i], feedbacks[i])
        self.client.post(reverse('freemoney:feedback'), postdata)

        page = self.client.get(reverse('freemoney:feedback'))
        ppp_result = self._parse_and_prepare_for_postback(page)
        feedbacks_by_user_i, _ = ppp_result
        for i in feedbacks.keys():
            self.assertHTMLEqual(feedbacks_by_user_i[i], feedbacks[i])

    def test_remove_one_feedback(self):
        """Given that four feedbacks are already in, replace one w/ blank."""
        feedbacks = {
                'b': "He had a lot to say.",
                'c': "He had a lot of nothin' to say.",
                'd': "We'll miss him.",
                'e': "We're gonna miss him."
        }
        for i in feedbacks.keys():
            PeerFeedback.objects.create(
                    peer=self.users[i]['peer_profile'],
                    application=self.application_so_far,
                    feedback=feedbacks[i]
            )

        page = self.client.get(reverse('freemoney:feedback'))
        original_c = feedbacks['c']
        feedbacks['c'] = ""
        ppp_result = self._parse_and_prepare_for_postback(page, feedbacks)
        feedbacks_by_user_i, postdata = ppp_result
        for i in feedbacks.keys():
            if i == 'c':
                self.assertHTMLEqual(feedbacks_by_user_i[i], original_c)
            else:
                self.assertHTMLEqual(feedbacks_by_user_i[i], feedbacks[i])
        self.client.post(reverse('freemoney:feedback'), postdata)

        page = self.client.get(reverse('freemoney:feedback'))
        ppp_result = self._parse_and_prepare_for_postback(page)
        feedbacks_by_user_i, _ = ppp_result
        for i in feedbacks.keys():
            self.assertHTMLEqual(feedbacks_by_user_i[i], feedbacks[i])

    def _parse_and_prepare_for_postback(self, page, new_feedbacks=None):
        feedbacks_by_user_i = {}
        postdata = utils.parse_formset_management_form(page.content)
        postdata['submit-type'] = 'next'
        feedback_name_re = re.compile(r'^(.*)-(\d+)-feedback$')

        ET = etree.parse(BytesIO(page.content), etree.HTMLParser())
        for textarea in ET.findall(r".//form//textarea"):
            match = feedback_name_re.match(textarea.get('name'))
            if match != None:
                field_name = "{}-{}-peer_id".format(*match.group(1, 2))
                hidden = ET.find(r'.//input[@name="{}"]'.format(field_name))
                peer = PeerProfile.objects.get(pk=int(hidden.get('value')))
                user_found = False
                for user_i in self.users.keys():
                    if peer == self.users[user_i]['peer_profile']:
                        feedbacks_by_user_i[user_i] = textarea.text
                        postdata[hidden.get('name')] = hidden.get('value')
                        if new_feedbacks != None and user_i in new_feedbacks:
                            new_feedback = new_feedbacks[user_i]
                            postdata[textarea.get('name')] = new_feedback
                        else:
                            postdata[textarea.get('name')] = textarea.text
                        user_found = True
                        break
                if not user_found:
                    raise ValueError('unrecognized peer textarea')

        return (feedbacks_by_user_i, postdata)
