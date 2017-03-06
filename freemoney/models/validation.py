import collections.abc


class CustomValidationIssue:
    """No-nonsense validation "issues" (not errors / exceptions).

    An individual issue will *always* have a section, field, and code
    associated with it. Furthermore, a code must be one of several well-known
    values. This alleviates the problem with ValidationError, which often
    contains bare strings.

    A section contains fields and a field contains numbered subfields. All
    three data are optional but the hierarchy must be maintained: a descriptor
    can only be given if all of its ancestors are given as well.

    Section and field are strings or None. Subfield is an integer or None.
    Code is a string which matches a member of CODES (see below).
    """

    # Well-known code values (and the only ones allowed!)
    CODES = ['required',   # information is missing that shouldn't be
             'invalid',    # input is malformed in some way
             'min-length', 'max-length', # too few or too many
             'prohibited'] # a business rule prevents some action

    def __init__(self, **kwargs):
        self.section = kwargs.pop('section', None)
        self.field = kwargs.pop('field', None)
        self.subfield = kwargs.pop('subfield', None)
        self.code = kwargs.pop('code')
        if len(kwargs) > 0:
            raise KeyError('illegal / invalid issue data: ' +
                            ', '.join(kwargs.keys()))
        elif not (isinstance(self.section, (str, type(None))) and
                  isinstance(self.field, (str, type(None))) and
                  isinstance(self.subfield, (int, type(None))) and
                  isinstance(self.code, str)):
            raise TypeError('incorrect type or types provided for issue')
        elif self.code not in CustomValidationIssue.CODES:
            raise KeyError('unknown code provided: {}'.format(self.code))
        else:
            hierarchy_finished = False
            for level_attr in ['section', 'field', 'subfield']:
                if getattr(self, level_attr) == None:
                    hierarchy_finished = True
                else:
                    if hierarchy_finished:
                        raise ValueError('illegal issue hierarchy at ' +
                                         level_attr)

    def __eq__(self, other):
        if isinstance(other, CustomValidationIssue):
            return (self.section == other.section and
                    self.field == other.field and
                    self.subfield == other.subfield and
                    self.code == other.code)
        else:
            return False

    def __str__(self):
        return str((self.section, self.field, self.subfield, self.code))


class CustomValidationIssueSet(collections.abc.MutableSet):
    """Set of CollectionValidationIssues with search and manipulation utils"""

    # see the search function
    GLOBAL = '__GLOBAL_reserved__'

    def __init__(self):
        # not a set because CustomValidationIssue is not hashable
        self._collection = []

    def __contains__(self, item):
        if isinstance(item, CustomValidationIssue):
            for issue in self._collection:
                if issue == item:
                    return True
        return False

    def __iter__(self):
        return iter(self._collection)

    def __len__(self):
        return len(self._collection)

    def add(self, new_issue):
        if isinstance(new_issue, CustomValidationIssue):
            if new_issue not in self:
                self._collection.append(new_issue)
        else:
            raise TypeError('can only add CustomValidationIssue instances')

    def discard(self, del_issue):
        for i in range(len(self._collection)):
            if self._collection[i] == del_issue:
                del self._collection[i]
                break

    def create(self, section=None, field=None, subfield=None, code=None):
        new_issue = CustomValidationIssue(section=section,
                                          field=field,
                                          subfield=subfield,
                                          code=code)
        self.add(new_issue)

    def search(self, *, section=None,
                        field=None,
                        subfield=None,
                        code=None,
                        aggregate=False,
                        discard=False):
        """Search issues, returning a new set with those matching the critera.

        The default value for the filter arguments is None, which matches any
        value. This is different than the constructor's behavior, which treats
        None as a "global" specifier for section, field, or subfield. To match
        a literal None, pass the value of the special attribute GLOBAL.

        When either None or GLOBAL values are used, the usual hierarchy rules
        apply (e.g., no meaningless searches for subfield without field).

        If the specification of section, field, and subfield will only match
        one target, you can pass aggregate=True to get a simple list of codes
        rather than a new CustomValidationIssueSet. Note: if more than one
        target was matched after all, an exception will be raised.

        If the discard=True flag is passed, any returned Issues will be
        deleted from the Set.
        """

        if not (isinstance(section, (str, type(None))) and
                isinstance(field, (str, type(None))) and
                isinstance(subfield, (int, str, type(None))) and
                isinstance(code, (str, type(None)))):
            raise TypeError('incorrect type or types provided for issue')
        elif (isinstance(subfield, str) and
              subfield != CustomValidationIssueSet.GLOBAL):
            raise TypeError('subfield must be integer, None, or GLOBAL')
        elif (isinstance(code, str) and
              code not in CustomValidationIssue.CODES):
            raise KeyError('unknown code provided: {}'.format(code))
        else:
            hierarchy = [('section', section),
                         ('field', field),
                         ('subfield', subfield)]
            # None is broader than GLOBAL, and GLOBAL is broader than specific
            had_none, had_global = False, False
            for level, value in hierarchy:
                if value is None:
                    had_none = True
                elif value == CustomValidationIssueSet.GLOBAL:
                    if had_none:
                        raise ValueError('illegal issue hierarchy at '+level)
                    had_global = True
                else:
                    if had_none or had_global:
                        raise ValueError('illegal issue hierarchy at '+level)

            matches = []
            new_collection = []
            for issue in self._collection:
                new_collection.append(issue)
                if section is not None:
                    if section == CustomValidationIssueSet.GLOBAL:
                        if None != issue.section:
                            continue
                    else:
                        if section != issue.section:
                            continue
                if field is not None:
                    if field == CustomValidationIssueSet.GLOBAL:
                        if None != issue.field:
                            continue
                    else:
                        if field != issue.field:
                            continue
                if subfield is not None:
                    if subfield == CustomValidationIssueSet.GLOBAL:
                        if None != issue.subfield:
                            continue
                    else:
                        if subfield != issue.subfield:
                            continue
                if code is not None and code != issue.code:
                    continue
                matches.append(issue)
                if discard:
                    new_collection.pop()
            self._collection = new_collection

            if aggregate:
                aggregate_specification = None
                for issue in matches:
                    if aggregate_specification == None:
                        aggregate_specification = (issue.section,
                                                   issue.field,
                                                   issue.subfield)
                    elif (aggregate_specification[0] != issue.section or
                          aggregate_specification[1] != issue.field or
                          aggregate_specification[2] != issue.subfield):
                        raise ValueError('aggregate spans multiple issues')
                return [issue.code for issue in matches]
            else:
                newset = CustomValidationIssueSet()
                for issue in matches:
                    newset.add(issue)
                return newset
