from collections import namedtuple
from django import forms
from django.shortcuts import render
from django.views.defaults import server_error
from freemoney.models import Application, ApplicantProfile, PeerFeedback
import re


from .common import WizardPageView


class FeedbackPage(WizardPageView):
    """Page where brothers (peers) are selected for receiving feedback."""

    page_name = 'feedback'
    required_fields = ['scholarshipaward_set']

    def render_page(self, context):
        existing_responses = list(self.application.peerfeedback_set.all())
        peer_metadata = []
        #TODO: fix ordering
        #for peer in PeerProfile.objects.order_by('display_name').iterator():
        for peer in ApplicantProfile.objects.iterator():
            if (peer.user != self.request.user and
                True):   # TODO: compare semester against "current" semester
                feedback = ""
                for response in existing_responses:
                    if response.peer == peer:
                        feedback = response.feedback
                        break
                peer_metadata.append({'peer_id': peer.pk,
                                    # TODO: use display name
                                    'peer_name': peer.user.username,
                                    'feedback': feedback,
                                    'expanded': (feedback != ""),
                                    'collapse_id': 'collapse_'+str(peer.pk)})
        peer_data = []
        for metadata in peer_metadata:
            peer_data.append({'peer_id': metadata['peer_id'],
                              'feedback': metadata['feedback']})
        context['formset'] = MultiplePeerFeedbackForm(initial=peer_data)
        context['peer_metadata'] = []
        for metadata, form in zip(peer_metadata, context['formset']):
            context['peer_metadata'].append(SinglePeerFeedbackMetadata(
                    form=form,
                    peer_name=metadata['peer_name'],
                    expanded=metadata['expanded'],
                    collapse_id=metadata['collapse_id']
            ))
        return render(self.request, 'feedback.html', context=context)

    def save_changes(self):
        formset = MultiplePeerFeedbackForm(self.request.POST)
        if not formset.is_valid():
            # TODO: error handling here
            return server_error(self.request)
        existing_responses = list(self.application.peerfeedback_set.all())
        existing_by_peer = {}
        for response in existing_responses:
            existing_by_peer[response.peer.pk] = response
        for form in formset:
            if int(form.cleaned_data['peer_id']) in existing_by_peer:
                response = existing_by_peer[form.cleaned_data['peer_id']]
                if re.match(r'^\s*$', form.cleaned_data['feedback']):
                    response.delete()
                else:
                    response.feedback = form.cleaned_data['feedback']
                    response.full_clean()
                    response.save()
            else:
                new_response = PeerFeedback.objects.create(
                        peer=ApplicantProfile.objects.get(
                                pk=form.cleaned_data['peer_id']
                        ),
                        feedback=form.cleaned_data['feedback'],
                        application=self.application
                )
        # success; proceed as usual to the next/previous/whatever step
        return None


class SinglePeerFeedbackForm(forms.Form):
    """Enables providing feedback for a single brother."""
    peer_id = forms.IntegerField(widget=forms.HiddenInput)
    feedback = forms.CharField(label="",
                               required=False,
                               widget=forms.Textarea(attrs={
                                    'rows': '3'
                               }))


SinglePeerFeedbackMetadata = namedtuple('SinglePeerFeedbackMetadata', [
    'form', 'peer_name', 'expanded', 'collapse_id'
])


MultiplePeerFeedbackForm = forms.formset_factory(
        SinglePeerFeedbackForm,
        extra=0
)
