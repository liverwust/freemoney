from collections import namedtuple
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from freemoney.models import Application, ScholarshipAward
import logging
import re


from .common import generate_nav_links


ScholarshipAwardSelection = namedtuple('ScholarshipAwardSelection', [
        'pk', 'name', 'description', 'selected'
])


@require_http_methods(['GET', 'HEAD', 'POST'])
def wizard_awards(request):
    """Page where the scholarship awards are selected."""
    my_path = reverse('freemoney:awards')

    if 'application' in request.session:
        application = Application.objects.get(
                pk=request.session['application']
        )
        if request.method == 'POST':
            selection_re = re.compile(r'^selection_(\d+)$')
            chosen_awards = set()
            for key, value in request.POST.items():
                match = selection_re.match(key)
                if match != None and value != "":
                    award_id = int(match.group(1))
                    award = ScholarshipAward.objects.get(
                            pk=award_id
                    )
                    chosen_awards.add(award)
            application.scholarshipaward_set.set(chosen_awards)
            application.full_clean()
            application.save()
            if request.POST.get('submit-type') == 'next':
                return redirect(reverse('freemoney:feedback'))
            elif request.POST.get('submit-type') == 'cancel':
                application.delete()
                del(request.session['application'])
                return redirect(reverse('freemoney:welcome'))
            else:
                return redirect(my_path)
        else:
            # TODO: sort them somehow
            all_awards = ScholarshipAward.objects.all()
            selected_awards = application.scholarshipaward_set.all()
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
        return redirect(reverse('freemoney:welcome'))
