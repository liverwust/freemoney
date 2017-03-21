from django.conf import settings
from django.db.models import (Manager,
                              Model,
                              CASCADE,
                              SET_NULL,
                              ForeignKey,
                              IntegerField,
                              ManyToManyField,
                              SlugField,
                              TextField)
from freemoney.models import (Application,
                              Award,
                              Semester)


class EssayManager(Manager):
    """Manager class for the EssayPrompt (and Essay, transitively) classes"""

    def latest_version_of(self, prompt_or_identifier):
        """Return the latest version of the EssayPrompt (or identifier)"""

        if isinstance(prompt_or_award, EssayPrompt):
            identifier = prompt_or_award.identifier
        else:
            identifier = prompt_or_award

        # TODO: de-duplicate this code against AwardManager...
        full_set = list(self.filter(identifier=identifier).all())
        tail = None
        for i in range(len(full_set)):
            new_tail = None
            for award in full_set:
                if award.previous_version == tail:
                    if new_tail is None:
                        new_tail = award
                    else:
                        raise ValueError('branch detected in linked list')
            if new_tail is None:
                raise ValueError('split detected in linked list')
            else:
                tail = new_tail
        return tail

    def for_award(self, award_or_identifier):
        """Return the (maybe-grouped) collection of EssayPrompts for an Award.

        The collection which is returned may itself contain collections. These
        sub-collections are "groups" of EssayPrompts, only one of which must
        be completed by an applicant. It is recommended to group them visually
        in some way.

        Note: as of now, if an essay prompt appears in multiple award
        collections, it must be grouped in *exactly the same way* as in every
        other award collection in which it appears.
        """

        if isinstance(award_or_identifier, Award):
            award = award_or_identifier
        else:
            award = Award.objects.latest_version_of(award_or_identifier)

        if award == 'giff_albright':
            return set([self.latest_version_of('giff_visit_review')])
        elif award == 'ean_hong':
            return set([set(['newmember_involvement_previous',
                             'involvement_outside']),
                        set(['newmember_coe_friends',
                             'established_coe_friends',
                             'newmember_coe_community_plans']),
                        set(['newmember_plans_from_others',
                             'established_your_legacy_friendship',
                             'established_your_legacy_accomplishments'])])
        elif award == 'ambassador':
            return set([set(['newmember_involvement_previous',
                             'involvement_outside']),
                        set(['newmember_previous_leadership',
                             'established_community_leadership']),
                        set(['newmember_greek_relations_plans',
                             'newmember_greek_relations_accomplishments',
                             'established_greek_relations_accomplishments'])])

    def for_application(self, application):
        """Return the full collection of EssayPrompts for a particular app."""

        essays = set()
        for award in application.award_set.iterator():
            for prompt_or_subset in self.for_award(award):
                if isinstance(prompt_or_subset, EssayPrompt):
                    essays.add(prompt_or_subset)
                else:
                    # TODO: implement the always-in-same-group rule as
                    # specified in the for_award docstring; for now, it is
                    # assumed that it is in effect
                    essays.add(prompt_or_subet)
        return essays

    def custom_validate_for_application(self, application, issues):
        """Perform check on an application (for CustomValidationIssues)"""

        all_responses = list(Essay.objects.filter(application=application))
        for response in all_responses:
            response.custom_validate(issues)

        for prompt_or_subset in self.for_application(application):
            if isinstance(prompt_or_subset, EssayPrompt):
                found = False
                for response in all_responses:
                    if response.prompt == prompt_or_subset:
                        found = True
                        break
                if not found:
                    issues.create(section='essay',
                                  field='[responses]',
                                  subfield=prompt_or_subset.pk,
                                  code='required')
            else:
                subset = prompt_or_subset
                all_found = True
                for prompt in subset:
                    found = False
                    for response in all_responses:
                        if response.prompt == prompt:
                            found = True
                            break
                    if not found:
                        all_found = False
                        break
                if not all_found:
                    for prompt in subset:
                        issues.create(section='essay',
                                      field='[response_groups]',
                                      subfield=prompt.pk,
                                      code='required')


class EssayPrompt(Model):
    """Represents a available essay prompt"""

    identifier = SlugField()
    prompt = TextField()
    word_limit = IntegerField()
    previous_version = ForeignKey('EssayPrompt',
                                  null=True,
                                  blank=True,
                                  on_delete=SET_NULL)
    application_set = ManyToManyField(Application, through='Essay')

    objects = EssayManager()


class Essay(Model):
    """Represents a response to an EssayPrompt"""

    application = ForeignKey('Application', on_delete=CASCADE)
    prompt = ForeignKey('EssayPrompt', on_delete=CASCADE)
    response = TextField()

    def custom_validate(self, issues):
        word_limit_with_grace = int(self.prompt.word_limit * 1.2)
        if len(self.response.split()) > word_limit_with_grace:
            self.issues.create(section='essay',
                               field='[responses]',
                               subfield=self.prompt.pk,
                               code='max-length')
