from django.conf import settings
from django.db.models import (Manager,
                              Model,
                              SET_NULL,
                              ForeignKey,
                              ManyToManyField,
                              SlugField,
                              TextField)
from freemoney.models import (Application,
                              Semester)


class AwardManager(Manager):
    """Manager class for the Award model (see below)"""

    def latest_version_of(self, identifier_or_award):
        """Return the latest version of the Award (or just an identifier)"""

        if isinstance(identifier_or_award, Award):
            identifier = identifier_or_award.identifier
        else:
            identifier = identifier_or_award

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

    def for_semester(self, semester=None):
        """Return the ordered list of Awards for a semester.

        The year is ignored. It is assumed that the caller is looking for the
        list of awards for the current Spring or Fall semester, and not
        historical data or a forecast regarding past or future semesters.

        By default, use the semester for FREEMONEY_DUE_DATE (in settings).
        """

        if semester == None:
            semester = Semester(settings.FREEMONEY_DUE_DATE)

        year = semester.date.year
        if semester == Semester(('Spring', year)):
            slugs = ['ean_hong', 'ambassador', 'giff_albright', 'joe_conway',
                     'dan_summers', 'navy_marine', 'excellence', 'pledge']
        elif semester == Semester(('Fall', year)):
            slugs = ['ean_hong', 'excellence', 'pledge']

        return [self.latest_version_of(slug) for slug in slugs]

    def custom_validate_for_application(self, application, issues):
        """Perform check on an application (for CustomValidationIssues)"""

        app_semester = Semester(application.due_at)

        all_endowments = set([self.latest_version_of(x) for x in [
                'giff_albright', 'joe_conway', 'ambassador', 'dan_summers',
                'navy_marine', 'excellence', 'pledge'
        ]])
        valid_endowments = set(all_endowments)
        valid_endowments &= set(self.for_semester(app_semester))

        expected_awards = set(self.for_semester(Semester(application.due_at)))
        if (application.semester_graduating is not None and
            application.semester_graduating <= Semester(application.due_at)):
            expected_awards -= all_endowments

        actual_awards = set()
        for index, selection in enumerate(application.award_set.iterator()):
            actual_awards.add(selection)
            if selection not in expected_awards:
                if selection in valid_endowments:
                    issues.create(section='award',
                                  field='selected',
                                  subfield=index,
                                  code='prohibited')
                    actual_awards.remove(selection)
                else:
                    issues.create(section='award',
                                  field='selected',
                                  subfield=index,
                                  code='invalid')
                    actual_awards.remove(selection)

        if len(actual_awards) < 1:
            issues.create(section='award',
                          code='min-length')


class Award(Model):
    """Represents a available scholarship award"""

    identifier = SlugField()
    name = TextField()
    description = TextField()
    previous_version = ForeignKey('Award',
                                  null=True,
                                  blank=True,
                                  on_delete=SET_NULL)
    application_set = ManyToManyField(Application)

    objects = AwardManager()
