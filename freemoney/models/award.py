from django.core.exceptions import ValidationError
from django.db.models import (Manager,
                              Model,
                              CASCADE,
                              BooleanField,
                              CharField,
                              ForeignKey,
                              IntegerField,
                              OneToOneField,
                              SlugField,
                              TextField)
from freemoney.models import (Semester,)


def get_semester_awards(semester):
    """Return the ordered list of all award shortnames available.

    The year is ignored. It is assumed that the caller is looking for the list
    of awards for the current Spring or Fall semester, and not historical data
    or a forecast regarding past or future semesters.
    """

    year = semester.date.year
    if semester == Semester('Spring', year):
        return ['ean_hong', 'ambassador', 'giff_albright', 'joe_conway',
                'dan_summers', 'navy_marine', 'excellence', 'pledge']
    elif semester == Semester('Fall', year):
        return ['ean_hong', 'excellence', 'pledge']


def custom_validate_award(application):
    """Validate the award selections associated with an Application"""

    def create_and_populate(self, application, *args, **kwargs):
        """Create a Picker and all of the necessary ScholarshipAwards"""

        picker = self.create(application=application, *args, **kwargs)

        def _copy_prompt(identifier, position):
            prompt = ScholarshipAwardPrompt.objects.get(identifier=identifier)
            picker.scholarshipaward_set.add(
                    position=position,
                    identifier=identifier,
                    name=prompt.name,
                    description=prompt.description,
                    chosen=False
            )

        # Upper limit should be many more than the number of awards
        autocount = iter(range(0, 10000))

        _copy_prompt('ean_hong', next(autocount))
        if application.application_semester.is_spring:
            _copy_prompt('ambassador', next(autocount))
            _copy_prompt('giff_albright', next(autocount))
            _copy_prompt('joe_conway', next(autocount))
            _copy_prompt('dan_summers', next(autocount))
            _copy_prompt('navy_marine', next(autocount))
        _copy_prompt('excellence', next(autocount))
        _copy_prompt('pledge', next(autocount))

        return picker


class ScholarshipAwardPicker(Model):
    """Scholarship award selections for a particular application"""

    objects = ScholarshipAwardPickerManager()
    application = OneToOneField('Application',
                                on_delete=CASCADE,
                                primary_key=True)

    def clean(self):
        errors = []

        expected_awards = set(['ean_hong', 'excellence', 'pledge'])
        if self.application.application_semester.is_spring:
            expected_awards |= set(['ambassador', 'giff_albright',
                                    'joe_conway', 'dan_summers',
                                    'navy_marine'])

        actual_by_id = {}
        nr_chosen = 0
        for selection in self.scholarshipaward_set.iterator():
            try:
                expected_awards.remove(selection.identifier)
                actual_by_id[selection.identifier] = selection
                if selection.chosen:
                    nr_chosen += 1
            except KeyError:
                errors.append(ValidationError(
                        'Extraneous scholarship award present in set',
                        code='award:invalid'
                ))

        if len(expected_awards) > 0:
            errors.append(ValidationError(
                    'Missing scholarship award(s): %(awards)s',
                    code='award:required',
                    params={'awards': ", ".join(expected_awards)}
            ))

        if nr_chosen < 1:
            errors.append(ValidationError(
                'Must select at least one scholarship award',
                code='award:min_length'
            ))

        endowment_set = set(['giff_albright', 'joe_conway', 'ambassador',
                             'dan_summers', 'navy_marine', 'excellence',
                             'pledge'])
        endowment_msg = 'Graduating seniors may only apply for the Hong award'
        endowment_selected = endowment_set.intersection(actual_by_id.keys())
        if endowment_selected != set():
            if (self.application.semester_graduating ==
                self.application.application_semester):
                errors.append(ValidationError(endowment_msg,
                                              code='award:senior_rule'))

        if len(errors) > 0:
            raise ValidationError(errors)


class ScholarshipAward(Model):
    """Represents an applicant's choice for a particular scholarship award"""

    picker = ForeignKey(ScholarshipAwardPicker, on_delete=CASCADE)
    position = IntegerField(help_text='List position relative to others')
    identifier = SlugField(help_text='Short name for a particular award')
    name = CharField(help_text='Display name for an award', max_length=255)
    description = TextField(
            help_text='Full description (archived alongside the application)'
    )
    chosen = BooleanField(help_text='Apply for this award?')


