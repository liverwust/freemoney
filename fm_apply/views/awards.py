from django import forms
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from fm_apply import models as fm_models


from .common import generate_nav_links


class AwardSelectionForm(forms.Form):
    """Determine which of the scholarship awards to apply for."""

    award_selections = forms.ModelMultipleChoiceField(
            queryset=fm_models.ScholarshipAwardPrompt.objects.all()
    )


@require_http_methods(['GET', 'HEAD', 'POST'])
def wizard_awards(request):
    """Page where the scholarship awards are selected."""

    if 'full_response' in request.session:
        full_response = request.session['full_response']
        if request.method == 'POST':
            form = AwardSelectionForm(request.POST)
            full_response.scholarshipawardprompt_set = form.award_selections
            full_response.full_clean()
            full_response.save()
            if request.POST.get('submit-type') == 'next':
                return redirect(reverse('fm_apply:feedback'))
            elif request.POST.get('submit-type') == 'cancel':
                full_response.delete()
                del(request.session['full_response'])
                return redirect(reverse('fm_apply:welcome'))
            else:
                return redirect(request.path)
        else:
            form = AwardSelectionForm()
            for award in full_response.scholarshipawardprompt_set:
                form.award_selections.append(award)
            context = generate_nav_links('awards')
            context['form'] = form
            context['buttons'] = ['cancel', 'next']
            return render('generic_wizard_form.html', context=context)
    else:
        return redirect(reverse('fm_apply:welcome'))
