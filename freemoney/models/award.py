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
                     'navy_marine', 'excellence', 'pledge']
        elif semester == Semester(('Fall', year)):
            slugs = ['ean_hong', 'excellence', 'pledge']

        return [self.latest_version_of(slug) for slug in slugs]

    def check_app_needs_finaid_activity(self, application):
        """True if an application needs finaid and activity pages"""
        checked_awards = set([self.latest_version_of('ean_hong'),
                              self.latest_version_of('ambassador'),
                              self.latest_version_of('giff_albright'),
                              self.latest_version_of('joe_conway'),
                              self.latest_version_of('navy_marine')])
        for selection in enumerate(application.award_set.iterator()):
            if selection in checked_awards:
                return True
        return False

    def check_app_needs_essay(self, application):
        """True if an application needs the essay page"""
        checked_awards = set([self.latest_version_of('ean_hong'),
                              self.latest_version_of('ambassador'),
                              self.latest_version_of('giff_albright')])
        for selection in enumerate(application.award_set.iterator()):
            if selection in checked_awards:
                return True
        return False

    def custom_validate_for_application(self, application, issues):
        """Perform check on an application (for CustomValidationIssues)"""

        this_semester_awards = self.for_semester(Semester(application.due_at))

        for index, selection in enumerate(application.award_set.iterator()):
            if selection not in this_semester_awards:
                issues.create(section='award',
                              field='[records]',
                              code='invalid')

            # Graduating seniors can only apply for certain awards
            if application.semester_graduating is None:
                pass
            elif (application.semester_graduating ==
                  Semester(application.due_at)):
                if selection.identifier in set(['giff_albright', 'joe_conway',
                                                'ambassador', 'navy_marine',
                                                'excellence', 'pledge',
                                                'ean_hong']):
                    issues.create(section='basicinfo',
                                  field='semester_graduating',
                                  code='prohibited')

            # Only AEs can apply for the Giff Albright award
            if application.major == '':
                pass
            elif application.major == 'Architectural Engineering':
                pass
            else:
                if selection.identifier == 'giff_albright':
                    issues.create(section='basicinfo',
                                    field='major',
                                    code='prohibited')

            # Only E SC and E MCH can apply for the Joe Conway award
            if application.major == '':
                pass
            elif application.major == 'Engineering Science':
                pass
            elif application.emch_minor == True:
                pass
            else:
                if selection.identifier == 'joe_conway':
                    issues.create(section='basicinfo',
                                    field='major',
                                    code='prohibited')

        if application.award_set.count() < 1:
            issues.create(section='award', code='min-length')


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
