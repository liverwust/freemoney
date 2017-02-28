import contextlib


class CustomValidationIssueManager:
    """No-nonsense validation "issue" management (not errors / exceptions).
    
    An individual error will *always* have a page, field, code, and message
    associated with it. This alleviates the problem with ValidationError,
    which often contains bare strings.

    While a message is displayed to the user, a code must be one of several
    well-known values.
    """

    CODES = ['required',   # information is missing that shouldn't be
             'invalid',    # input is malformed in some way
             'min-length', 'max-length', # too few or too many
             'prohibited'] # a business rule prevents some action

    DONTCARE = '__IGNORE__reserved__'

    class ContextProxy:
        def __init__(self, host, **kwargs):
            self._host = host
            self._kwargs = kwargs

        def add(self, **kwargs):
            kwargs.update(self._kwargs)
            self._host.add(**kwargs)

        def search(self, **kwargs):
            kwargs.update(self._kwargs)
            return self._host.search(**kwargs)

    def __init__(self):
        self._collection = []

    def add(self, *, page=None, field=None, code=None, message=None):
        """Append an issue to this manager's collection.

        The code and message must be provided. Any of the following
        combinations of page and field are allowed:
          * page='xxxx', field='yyyy': the issue corresponds to a specific
            field on a specific page
          * page='xxxx', field=None: the issue applies to a whole page
          * page=None, field=None: the issue applies to the entire wizard
        But not this combination, which is meaningless:
          * page=None, field='yyyy': will result in an exception
        """

        if not (isinstance(page, (str, type(None))) and
                isinstance(field, (str, type(None))) and
                isinstance(code, str) and
                isinstance(message, str)):
            raise TypeError('incorrect type or types provided for issue')
        elif page == None and field != None:
            raise ValueError('meaningless combination: field w/o a page')
        elif code not in CustomValidationIssueManager.CODES:
            raise ValueError('unknown code provided: {}'.format(code))
        else:
            # Collapse multiple issues into a sub-collection, if necessary
            existing = self.search(page=page, field=field)
            if len(existing) == 0:
                self._collection.append((page, field, code, message))
            elif len(existing) == 1:
                for i in range(len(self._collection)):
                    other = self._collection[i]
                    o_page, o_field, o_code, o_message = other
                    if o_page == page and o_field == field:
                        if (isinstance(o_code, str) and
                            isinstance(o_message, str)):
                            new_codes = [o_code, code]
                            new_messages = [o_message, message]
                        else:
                            new_codes = list(o_code)
                            new_codes.append(code)
                            new_messages = list(o_message)
                            new_messages.append(message)
                        self._collection[i] = (page, field, new_codes,
                                               new_messages)
                        break
            else:
                raise RuntimeError('internal logic problem; abort!')

    def search(self, *, page=DONTCARE, field=DONTCARE,
                        code=DONTCARE, expand=False):
        """Search for issues which match the given critera.

        Please note that None is a meaningful value, at least in the context
        of the page and field arguments. To indicate that a particular
        argument should not restrict the results, pass DONTCARE (the default).

        You cannot search on a message -- it is supposed to be freeform. Use
        the code instead.

        Pass expand=True to return a separate tuple for every individual
        page/field combination, rather than a single combined tuple for each
        such combination.
        """

        matches = []
        for issue in self._collection:
            if (page != CustomValidationIssueManager.DONTCARE and
                page != issue[0]):
                continue
            if (field != CustomValidationIssueManager.DONTCARE and
                field != issue[1]):
                continue
            if (code != CustomValidationIssueManager.DONTCARE and
                code != issue[2]):
                continue

            if not expand or (isinstance(issue[2], str) and
                              isinstance(issue[3], str)):
                matches.append(issue)
            else:
                for code, message in zip(issue[2], issue[3]):
                    matches.append((issue[0], issue[1], code, message))
        return matches

    def for_page(self, page, include_generic=True):
        """Returns issues affecting a given page, maybe plus page=None."""

        if page == CustomValidationIssueManager.DONTCARE:
            raise ValueError('use DONTCARE with search, not with on_page')
        else:
            matches = self.search(page=page)
            if page != None and include_generic:
                generic_matches = self.search(page=None, field=None)
                # there will never be any intersection / overlap between
                # page=page and page=None (assuming page != None), so just go
                # ahead and extend
                matches.extend(generic_matches)
            return matches

    @contextlib.contextmanager
    def context(self, *, page=DONTCARE, field=DONTCARE, code=DONTCARE):
        """Restrict (inside a with-block) add and search operations.

        This context manager yields a proxy object upon which .add and .search
        operations are limited by the provided criteria, but otherwise act as
        if they directly call the manager functions described above.

        As with .search(), there is no message argument provided here.
        """

        kwargs = {'page': page, 'field': field, 'code': code}
        for key in list(kwargs.keys()):
            if kwargs[key] == CustomValidationIssueManager.DONTCARE:
                del kwargs[key]
        yield CustomValidationIssueManager.ContextProxy(self, **kwargs)
