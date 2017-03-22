from django.conf import settings
from django.forms import (CharField,
                          Form,
                          formset_factory,
                          HiddenInput,
                          IntegerField,
                          Textarea)
from django.template import RequestContext, Template
from django.utils.safestring import mark_safe
from freemoney.models import (Application,
                              ApplicantProfile,
                              Essay,
                              EssayPrompt)
import re


from .common import WizardPageView
from .finaid import FinancialAidPage


class EssayPage(WizardPageView):
    """Page where brothers (peers) can answer required essays"""

    page_name = 'essay'
    prev_page = FinancialAidPage

    @staticmethod
    def progress_sentry(issues):
        if len(issues.search(section='essay')) > 0:
            return False
        else:
            return True

    def prepopulate_form(self):
        # TODO: should probably become an official part of common
        self._form_elements = []
        initial_data = []
        existing_responses = list(Essay.objects.filter(
                application=self.application
        ).all())
        all_prompts = EssayPrompt.objects.for_application(self.application)
        for subset_index, prompt_or_subset in enumerate(all_prompts):
            if isinstance(prompt_or_subset, EssayPrompt):
                subset = [prompt_or_subset]
            else:
                subset = prompt_or_subset

            for prompt in subset:
                initial_data_row = {'prompt_id': prompt.pk}
                for response in existing_responses:
                    if response.prompt == prompt:
                        initial_data_row['response'] = response.response
                        break
                if 'response' not in initial_data_row:
                    initial_data_row['response'] = ''
                self._form_elements.append((
                        prompt.pk,
                        prompt.prompt,
                        subset_index,
                        prompt.word_limit,
                        []
                ))
                initial_data.append(initial_data_row)

        return EssayFormSet(initial=initial_data)

    def parse_form(self):
        return EssayFormSet(self.request.POST)

    def save_changes(self):
        existing_responses = list(Essay.objects.filter(
                application=self.application
        ).all())
        all_prompts = EssayPrompt.objects.for_application(self.application)
        preserved_responses = []
        for individual in self.form:
            the_prompt = None
            for prompt in all_prompts:
                if isinstance(prompt, list):
                    for subprompt in prompt:
                        if subprompt.pk == individual.cleaned_data['prompt_id']:
                            the_prompt = subprompt
                            break
                else:
                    if prompt.pk == individual.cleaned_data['prompt_id']:
                        the_prompt = prompt
                        break
            if the_prompt is None:
                raise KeyError('bad prompt id')

            existing_response = None
            for response in existing_responses:
                if response.prompt.pk == the_prompt.pk:
                    existing_response = response
                    break

            if re.match(r'^\s*$', individual.cleaned_data['response']):
                if existing_response is not None:
                    existing_response.delete()
            else:
                if existing_response is None:
                    new_response = Essay.objects.create(
                            application=self.application,
                            prompt=the_prompt,
                            response=individual.cleaned_data['response']
                    )

                    preserved_responses.append(new_response)
                else:
                    new_response = individual.cleaned_data['response']
                    existing_response.response = new_response
                    existing_response.full_clean()
                    existing_response.save()
                    preserved_responses.append(existing_response)

        for existing_response in existing_responses:
            found = False
            for preserved_response in preserved_responses:
                if preserved_response == existing_response:
                    found = True
                    break
            if not found:
                existing_response.delete()

    def add_issues_to_form(self):
        for issue in self.issues.search(section='essay', discard=True):
            if issue.field == '[responses]':
                for element in self._form_elements:
                    if element[0] == issue.subfield:
                        if issue.code == 'required':
                            message = 'This essay prompt must be answered'
                        elif issue.code == 'max-length':
                            message = 'You have exceeded the word limit'
                        else:
                            message = 'Unknown error'
                        element[4].append(message)
                        break
            if issue.field == '[response_groups]':
                group_id = None
                for element in self._form_elements:
                    if element[0] == issue.subfield:
                        group_id = element[2]
                        break
                if group_id is not None:
                    for element in self._form_elements:
                        if element[2] == group_id:
                            if issue.code == 'required':
                                message = 'At least one essay prompt within this group must be answered'
                            else:
                                message = 'Unknown error (group)'
                            element[4].append(message)

    def finalize_context(self):
        self.context['the_section'] = '<div class="well essay_subset">'

        single_instructions ="<p>Please answer this essay question.</p><hr />"
        multi_instructions = "<p>Please answer <em>only one</em> of the essay questions in this group.<p><hr />"

        if len(self.form) > 1:
            if self._form_elements[0][2] == self._form_elements[1][2]:
                # First two essays are in the same subset
                self.context['the_section'] += multi_instructions
            else:
                self.context['the_section'] += single_instructions
        elif len(self.form) == 1:
            self.context['the_section'] += single_instructions
        else:
            self.context['the_section'] += 'No essay questions for your chosen awards.</div>'
        need_instructions = False

        for index in range(len(self.form)):
            if need_instructions == True:
                if index + 1 >= len(self.form):
                    # obviously no additional subset items past the end
                    self.context['the_section'] += single_instructions
                elif (self._form_elements[index][2] ==
                      self._form_elements[index + 1][2]):
                    self.context['the_section'] += multi_instructions
                else:
                    self.context['the_section'] += single_instructions
                need_instructions = False

            self.context['the_section'] += '<p><strong>Question: </strong>'
            self.context['the_section'] += self._form_elements[index][1]
            self.context['the_section'] += ' <em>('
            self.context['the_section'] += str(self._form_elements[index][3])
            self.context['the_section'] += ' word limit)</em>'
            self.context['the_section'] += '</p>'

            template = Template('{% load bootstrap3 %}{% bootstrap_field field show_label=False %}')
            temp_ctx = RequestContext(self.request)
            temp_ctx.update({'field': self.form[index]['prompt_id']})
            self.context['the_section'] += template.render(temp_ctx)

            template = Template('{% load bootstrap3 %}{% bootstrap_field field show_label=False %}')
            temp_ctx = RequestContext(self.request)
            temp_ctx.update({'field': self.form[index]['response']})
            self.context['the_section'] += template.render(temp_ctx)

            if len(self._form_elements[index][4]) > 0:
                error_list = '<ul></ul>'
                for error in self._form_elements[index][4]:
                    insert_at = error_list.find('</ul>')
                    error_list = (error_list[0:insert_at] +
                                    '<li>{}</li>'.format(error) +
                                    error_list[insert_at:])
            else:
                error_list = ''
            self.context['the_section'] += error_list

            if index + 1 >= len(self.form):
                # obviously the end of the current subset
                self.context['the_section'] += '</div>'
            elif (self._form_elements[index][2] ==
                  self._form_elements[index + 1][2]):
                # amidst a subset; add a horizontal rule for clarity
                self.context['the_section'] += '<hr />'
            else:
                # the end of this subset and the beginning of another
                self.context['the_section'] += '</div>'
                self.context['the_section'] += '<div class="row">&nbsp;</div>'
                self.context['the_section'] += '<div class="well essay_subset">'
                need_instructions = True

        self.context['the_section'] = mark_safe(self.context['the_section'])


class EssayForm(Form):
    """Enables providing a single essay response"""

    prompt_id = IntegerField(widget=HiddenInput)
    response = CharField(required=False, widget=Textarea(attrs={'rows': 3}))


EssayFormSet = formset_factory(EssayForm, extra=0)
