from collections import namedtuple
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from fm_apply import models as fm_models
import re


from .common import generate_nav_links


ScholarshipAwardSelection = namedtuple('ScholarshipAwardSelection', [
        'pk', 'name', 'description', 'selected'
])


@require_http_methods(['GET', 'HEAD', 'POST'])
def wizard_awards(request):
    """Page where the scholarship awards are selected."""
    my_path = reverse('fm_apply:awards')

    if 'full_response' in request.session:
        full_response = fm_models.ApplicantResponse.objects.get(
                pk=request.session['full_response']
        )
        if request.method == 'POST':
            selection_re = re.compile(r'^selection_(\d+)$')
            chosen_awards = set()
            for key, value in request.POST.items():
                match = selection_re.match(key)
                if match != None and value != "":
                    award_id = int(match.group(1))
                    award = fm_models.ScholarshipAwardPrompt.objects.get(
                            pk=award_id
                    )
                    chosen_awards.add(award)
            full_response.scholarshipawardprompt_set.set(chosen_awards)
            full_response.full_clean()
            full_response.save()
            if request.POST.get('submit-type') == 'next':
                return redirect(reverse('fm_apply:feedback'))
            elif request.POST.get('submit-type') == 'cancel':
                full_response.delete()
                del(request.session['full_response'])
                return redirect(reverse('fm_apply:welcome'))
            else:
                return redirect(my_path)
        else:
            # TODO: sort them somehow
            all_awards = fm_models.ScholarshipAwardPrompt.objects.all()
            selected_awards = full_response.scholarshipawardprompt_set.all()
            selections = []
            for award in all_awards:
                selection = ScholarshipAwardSelection(
                        pk='selection_{}'.format(award.pk),
                        selected=(award in selected_awards),
                        name=award.name,
                        description=award.description
                )
                selections.append(selection)
            context = generate_nav_links('awards')
            context['postback'] = my_path
            context['selections'] = selections
            context['buttons'] = ['cancel', 'next']
            return render(request,
                          'awards.html',
                          context=context)
    else:
        return redirect(reverse('fm_apply:welcome'))
