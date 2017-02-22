from collections import namedtuple
from django.shortcuts import render
from freemoney.models import Application, ScholarshipAward
import re


from .common import WizardView


ScholarshipAwardSelection = namedtuple('ScholarshipAwardSelection', [
        'pk', 'name', 'description', 'selected'
])


class AwardsPage(WizardView):
    """Page where the scholarship awards are selected."""

    page_name = 'awards'

    def render_page(self, context):
        # TODO: sort them somehow
        all_awards = ScholarshipAward.objects.all()
        selected_awards = self.application.scholarshipaward_set.all()
        selections = []
        for award in all_awards:
            selection = ScholarshipAwardSelection(
                    pk='selection_{}'.format(award.pk),
                    selected=(award in selected_awards),
                    name=award.name,
                    description=award.description
            )
            selections.append(selection)
        context['selections'] = selections
        return render(self.request, 'awards.html', context=context)

    def save_changes(self):
        selection_re = re.compile(r'^selection_(\d+)$')
        chosen_awards = set()
        for key, value in self.request.POST.items():
            match = selection_re.match(key)
            if match != None and value != "":
                award_id = int(match.group(1))
                award = ScholarshipAward.objects.get(pk=award_id)
                chosen_awards.add(award)
            self.application.scholarshipaward_set.set(chosen_awards)
            self.application.full_clean()
            self.application.save()
        return True
