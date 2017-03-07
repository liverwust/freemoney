from django.conf import settings
from django.contrib.auth import get_user_model
from django.forms import (CharField,
                          Form,
                          formset_factory,
                          HiddenInput,
                          IntegerField,
                          Textarea)
from freemoney.models import (Application,
                              ApplicantProfile,
                              Feedback)
import re


from .common import WizardPageView
from .award import AwardPage


class FeedbackPage(WizardPageView):
    """Page where brothers (peers) are selected for receiving feedback."""

    page_name = 'feedback'
    prev_page = AwardPage

    @staticmethod
    def progress_sentry(issues):
        if len(issues.search(section='feedback')) > 0:
            return False
        else:
            return True

    def prepopulate_form(self):
        initial_data = []
        existing_feedbacks = Feedback.objects.filter(
                application=self.application
        ).all()
        for peer in Feedback.objects.get_eligible_peers():
            if peer != self.applicant:
                new_data = {'peer_id': peer.pk,
                            'peer_name': '{} {}'.format(peer.user.first_name,
                                                        peer.user.last_name)}
                for feedback in existing_feedbacks:
                    if feedback.peer == peer:
                        new_data['feedback'] = feedback.feedback
                        break
                if 'feedback' not in new_data:
                    new_data['feedback'] = ''
                initial_data.append(new_data)
        return FeedbackFormSet(initial=initial_data)

    def parse_form(self):
        return FeedbackFormSet(self.request.POST)

    def save_changes(self):
        existing_feedbacks = Feedback.objects.filter(
                application=self.application
        ).all()
        existing_by_peer = {}
        for feedback in existing_feedbacks:
            existing_by_peer[feedback.peer.pk] = feedback

        for individual in self.form:
            peer_id = individual.cleaned_data['peer_id']
            if peer_id != self.applicant.pk:
                if peer_id in existing_by_peer:
                    feedback = existing_by_peer[peer_id]
                    if re.match(r'^\s*$', individual.cleaned_data['feedback']):
                        feedback.delete()
                    else:
                        feedback.feedback = individual.cleaned_data['feedback']
                        feedback.full_clean()
                        feedback.save()
                else:
                    if re.match(r'^\s*$', individual.cleaned_data['feedback']):
                        pass
                    else:
                        new_feedback = Feedback.objects.create(
                                peer=ApplicantProfile.objects.get(pk=peer_id),
                                feedback=individual.cleaned_data['feedback'],
                                application=self.application
                        )

    def add_issues_to_form(self):
        if (len(self.issues.search(section='feedback',
                                   code='min-length',
                                   discard=True)) > 0):
            self.form._non_form_errors.append(
                    'Must provide at least {} reviews'.format(
                            settings.FREEMONEY_MIN_FEEDBACK_COUNT
                    )
            )
        for issue in self.issues.search(section='award', discard=True):
            self.form._non_form_errors.append(str(issue))


class FeedbackForm(Form):
    """Enables providing feedback for a single brother."""

    peer_id = IntegerField(widget=HiddenInput)
    peer_name = CharField()
    feedback = CharField(required=False, widget=Textarea)


FeedbackFormSet = formset_factory(FeedbackForm, extra=0)
