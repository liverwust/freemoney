#TODO: not yet finished!!!

from django import forms
from django.contrib import auth
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.html import escape
from django.views.decorators.http import require_http_methods
from fm_apply import models as fm_models


from .common import generate_nav_links, fields_required_beyond_step


class PeerNameWidget(forms.Widget):
    """Represents the name of a peer who could receive feedback."""

    def format_value(self, value):
        return value

    def render(name, value, attrs=None):
        return '<b>{}</b>'.format(escape(value))


class SinglePeerFeedbackForm(forms.Form):
    """Enables selecting a single brother and providing feedback for him."""

    selected = forms.BooleanField(required=False, initial=False)
    peer_name = forms.CharField(max_length=255, widget=PeerNameWidget)
    peer_id = forms.
    feedback = forms.TextField(required=False)

    def clean(self):
        if self.cleaned_data['selected']:
            if ('feedback' not in self.cleaned_data or
                self.cleaned_data['feedback'] == None or
                self.cleaned_data['feedback'] == ''):
                raise ValidationError('missing feedback', code='required')
        else:
            if ('feedback' in self.cleaned_data and
                self.cleaned_data['feedback'] != None and
                self.cleaned_data['feedback'] != ''):
                raise ValidationError('extraneous feedback', code='invalid')



@require_http_methods(['GET', 'HEAD', 'POST'])
@fields_required_beyond_step('awards', ['scholarshipawardresponse_set'])
def wizard_feedback(request):
    """Page where brothers (peers) are selected for receiving feedback."""

    if 'full_response' in request.session:
        full_response = fm_models.ApplicantResponse.objects.get(
                pk=request.session['full_response']
        )
        if request.method == 'POST':
            records = _obtain_full_feedback_list()
            formset_class = forms.formset_factory(SinglePeerFeedbackForm,
                                                  initial=records)
            formset = formset_class(request.POST)
            # TODO: better way to do this than deleting?
            fm_models.PeerFeedbackResponse.objects.filter(
                    full_response=full_response
            )
            for form in formset:
                fm_models.PeerFeedbackResponse.objects.create(
                        full_response=full_response,
                        peer=auth.models.User.filter(

def _obtain_full_feedback_list():
    """Obtain the records for all possible peer feedback recipients."""

    records = []
    existing_records = fm_models.PeerFeedbackResponse.objects.filter(
            full_response=full_response,
    )
    nonrepresented_peers = auth.models.User.objects.all()

    for existing_record in existing_records:
        for i in range(len(nonrepresented_peeers)):
            if nonrepresented_peers[i] == existing_record.peer:
                del(nonrepresented_peers[i])
                break
        record = {}
        record['selected'] = True
        record['peer_name'] = existing_record.peer.get_full_name()
        record['feedback'] = existing_record.feedback
        records.append(record)

    for nonrepresented_peer in nonrepresented_peers:
        record = {}
        record['selected'] = False
        record['peer_name'] = nonrepresented_peer.get_full_name()
        record['feedback'] = ''
        records.append(record)

    # TODO: sort by last name, probably
    return sorted(records, lambda x: x.peer_name)

#            elif 'peerfeedbackresponse_set' in exc.error_dict:
#                return redirect(reverse('feedback') + '?with=errors')
#            elif set() != set(exc.error_dict.keys()).intersection(set([
#                    'name', 'address', 'phone', 'psu_email', 'psu_id',
#                    'date_initiated', 'date_graduating', 'cumulative_gpa',
#                    'semester_gpa', 'in_state_tuition'])):
