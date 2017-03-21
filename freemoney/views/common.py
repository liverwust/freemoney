from django.conf import settings
from django.contrib.messages import (add_message,
                                     get_messages,
                                     INFO,
                                     ERROR)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.forms import Form, BaseFormSet
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django.views.defaults import server_error
from freemoney.models import (Application,
                              ApplicantProfile,
                              Award,
                              CustomValidationIssue,
                              CustomValidationIssueSet,
                              Semester)


class WizardPageView(LoginRequiredMixin, View):
    """Class-based view for wizard pages.

    This base class is a skeleton implementation of the GET and POST views for
    all of the actual wizard pages.

    A subclass should not override get() and post(), but should define these
    (optional, unless otherwise specified) methods and attributes:
    * (required) class attribute page_name: short name from PAGES table
    * class attribute prev_page: WizardPageView subclass for the previous page
    * class attribute progress_sentry(): return False if overwhelmed by issues
    * instance method prepopulate_form: return a Form or FormSet on GET
    * instance method parse_form: return a Form or FormSet following POST
    * instance method save_changes: fields -> DB, ignoring model validation
    * instance method add_issues_to_form: convert model CVIssue -> form VError
    * instance method finalize_context: add extra info to template context

    These hooks and data are used in conjunction with the rendering procedure,
    which follows these steps (note: later steps can use earlier variables):
    1.  set self.request, self.applicant, self.application, and self.issues
    2.  call progress_sentry through prev_page chain, but *not* for this page
    3.  set self.form to result of prepopulate_form (GET) or parse_form (POST)
    4.  call save_changes if the form is bound and the *form* fields are valid
        NOTE: this ^^ is called and should work regardless of *model* validity
    5.  update self.issues with any issues detected following save_changes
    6.  if attempting to go to the next page, verify with self.progress_sentry
    7.  if blocked or rendering this page w/ errors, call add_issues_to_form
    8.  self.context is generated with common info (e.g., buttons and URLs)
    9.  call finalize_context, which should add info as needed to self.context
    10. template is rendered using the page_name set by the subclass
    """

    # (short name, display name)
    PAGES = [('welcome', 'Welcome'),
             ('award',  'Choose Awards'),
             ('basicinfo', 'Basic Information')]
#             ('finaid', 'Financial Aid'),

    # don't allow PUT, PATCH, DELETE, or TRACE
    http_method_names = ['get', 'post', 'head', 'options']

    def __init__(self, *args, **kwargs):
        super(WizardPageView, self).__init__(*args, **kwargs)
        self.request = None
        self.applicant = None
        self.application = None
        self.issues = None
        self.form = None
        self.context = None

    def _initialize_for_request(self, request):
        self.request = request

        try:
            self.applicant = self.request.user.applicantprofile
            if self.applicant.must_change_password:
                # TODO: forced password change
                return server_error(self.request)
        except ObjectDoesNotExist:
            # TODO: make a landing page for non-applicant users
            return server_error(self.request)

        try:
            self.application = self.applicant.current_application
            if self.application.submitted:
                return redirect(self._uri_of('submitted'))
        except ObjectDoesNotExist:
            # TODO: same landing page as for non-applicant users
            return server_error(self.request)

        self.issues = CustomValidationIssueSet()
        self.application.custom_validate(self.issues)

        self._my_pages = []
        self._page_index = None
        needs_finaid = Award.objects.check_app_needs_finaid(self.application)
        needs_essay = Award.objects.check_app_needs_essay(self.application)
        for index, names in enumerate(WizardPageView.PAGES):
            short_name, long_name = names
            if ((not needs_finaid and short_name == 'finaid') or
                (not needs_essay and short_name == 'essay')):
                if type(self).page_name == short_name:
                    return redirect(self._uri_of(self._my_pages[-1][0]))
                else:
                    continue
            if type(self).page_name == short_name:
                self._page_index = index
            self._my_pages.append((short_name, long_name))
        if self._page_index == None:
            raise KeyError('invalid page name: {}'.format(page_name))

        failing_sentry = self._find_failing_sentry(including_me=False)
        if failing_sentry is not None:
            add_message(self.request, ERROR,
                        'Please complete this section first')
            return redirect(self._uri_of(failing_sentry.page_name))

    def _find_failing_sentry(self, including_me):
        if including_me:
            checked_class = type(self)
        else:
            checked_class = getattr(self, 'prev_page', None)

        while checked_class is not None:
            if not hasattr(checked_class, 'progress_sentry'):
                checked_class = getattr(checked_class, 'prev_page', None)
            elif checked_class.progress_sentry(self.issues):
                checked_class = getattr(checked_class, 'prev_page', None)
            else:
                return checked_class

        # all sentry checks succeeded
        return None

    def _generate_base_context(self):
        base_context = {
                'steps': [],
                'currentstep': type(self).page_name,
                'postback': self._uri_of(self.page_name),
                'deadline': settings.FREEMONEY_DUE_DATE.date,
                'buttons': [x[0] for x in self._calculate_valid_buttons()],
        }
        for short_name, long_name in self._my_pages:
            is_active = (short_name == type(self).page_name)
            base_context['steps'].append((long_name, is_active))

        base_context['errors'] = []
        for message in get_messages(self.request):
            if message.level == ERROR:
                base_context['errors'].append(message.message)
        return base_context

    def _uri_of(self, name):
        return reverse('freemoney:{}'.format(name))

    def _calculate_valid_buttons(self):
        buttons = [('restart', None)]
        if self._page_index > 0:
            buttons.append(('save', None))
            prev_page = self._my_pages[self._page_index - 1]
            buttons.append(('prev', prev_page))
        if self._page_index + 1 < len(self._my_pages):
            next_page = self._my_pages[self._page_index + 1]
            buttons.append(('next', next_page))
        elif self._page_index + 1 == len(self._my_pages):
            buttons.append(('submit', None))
        return buttons

    def get(self, request):
        """Don't override this method, but use the hooks instead"""

        if type(self) == WizardPageView:
            raise NotImplementedError('WizardPageView is an abstract base')
        else:
            error_response = self._initialize_for_request(request)
            if error_response is not None:
                return error_response

        self.form = self.prepopulate_form()

        base_context = self._generate_base_context()
        if len(base_context['errors']) > 0:
            self.add_issues_to_form()

        self.context = base_context
        self.context['form'] = self.form
        self.finalize_context()

        return render(self.request,
                      self.page_name + '.html',
                      context=self.context)

    def post(self, request):
        """Don't override this method, but use the hooks instead"""

        if type(self) == WizardPageView:
            raise NotImplementedError('WizardPageView is an abstract base')
        else:
            error_response = self._initialize_for_request(request)
            if error_response is not None:
                return error_response

        self.form = self.parse_form()
        if self.form is None or self.form.is_valid():
            if self.form is not None:
                self.save_changes()

            submit_type = request.POST.get('submit-type', default=None)

            if submit_type == 'submit':
                self.application.submitted = True

            self.issues = CustomValidationIssueSet()
            self.application.custom_validate(self.issues)

            if submit_type == 'restart':
                self.application.delete()
                self.application = Application.objects.create(
                        due_at=settings.FREEMONEY_DUE_DATE,
                        applicant=self.applicant
                )
                self.applicant.full_clean()
                self.applicant.save()
                add_message(self.request, INFO,
                            'Application was successfully restarted')
                return redirect(self._uri_of(self._my_pages[0][0]))
            else:
                including_me = (submit_type != 'prev')
                failing_sentry = self._find_failing_sentry(including_me)
                if failing_sentry is None:
                    if submit_type == 'prev':
                        redirect_to = self._my_pages[self._page_index - 1][0]
                    elif submit_type == 'next':
                        redirect_to = self._my_pages[self._page_index + 1][0]
                    elif submit_type == 'submit':
                        self.application.full_clean()
                        self.application.save()
                        redirect_to = 'submitted'
                    else:
                        redirect_to = self._my_pages[self._page_index][0]
                    return redirect(self._uri_of(redirect_to))
                else:
                    add_message(self.request,
                                ERROR,
                                'Please fix form errors below before proceeding'
                    )
                    return redirect(
                            self._uri_of(failing_sentry.page_name)
                    )

    def prepopulate_form(self):
        """Return a Form or FormSet using DB data (None for pages w/o form)"""
        return None

    def parse_form(self):
        """Use POSTDATA to return a Form(Set) (None for pages w/o form)"""
        return None

    def save_changes(self):
        """Persist user-specified changes to the model layer (database).

        At this point, self.form is intialized (if the view is supposed to
        have one) and is guaranteed to be "valid" with respect to
        model/view-layer validation logic.

        This method is expected to save all of the form information to the
        database without regard for model-level validation, in order to enable
        saving incomplete applications. Model-level validation is handled
        elsewhere, by other hooks.
        """
        pass

    def add_issues_to_form(self):
        """Convert model-level CustomValidationIssues to view-level Errors.

        This method is called as late as possible; specifically, it is called
        only when the user attempts to navigate to the next or final step in
        the wizard. Before being called, self.form and self.issues will both
        be made available.
        """
        pass

    def finalize_context(self):
        """Add any extra information to self.context, as required"""
        pass
