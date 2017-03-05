from datetime import datetime, timedelta, timezone
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django.views.defaults import server_error
from freemoney.models import (Application,
                              ApplicantProfile,
                              CustomValidationIssue,
                              CustomValidationIssueSet,
                              Semester)


class WizardPageView(LoginRequiredMixin, View):
    """Class-based view for wizard pages.

    This base class is a skeleton implementation of the GET and POST views for
    all of the actual wizard pages. Rather than overriding get() and post(),
    subclasses should use the instance variables and hooks provided by this
    class.

    A subclass should set its page_name attribute to its short name (selected
    from the PAGES constant).

    Generally, a page is rendered using the procedure outlined below. Except
    where specific return values are required, a hook can return None (the
    default in Python) to allow the procedure to continue or an HttpResponse
    in order to immediately stop processing and send the response to the user.

    The rendering steps (where data from earlier steps can be reused later):
    1.  Authenticate the user using the Django auth backend
    2.  Copy the HttpRequest to self.request
    3.  Authenticate user and set self.applicant to their ApplicantProfile
    4.  Ensure that an application exists and set self.application
    5.  hook_check_can_access: return False to block access b/c of validation
    6.  Determine if errors should be shown and set self.show_errors (bool)
    7.  hook_save_changes (POST): use POSTDATA to modify the Application / DB
    8.  Generate basic self.context with common info (e.g., nav buttons)
    9.  hook_check_can_proceed (POST): return False to block progress here
    10. hook_prepare_context (GET): add template information to self.context
    11. Render the template (GET) for the wizard page (using self.context)
    """

    # (short name, display name)
    PAGES = [('welcome', 'Welcome'),
             ('award',  'Choose Awards'),
             ('feedback', 'Peer Feedback'),
             ('dummy', 'Dummy Page')] # TODO: get rid of this last line

    # don't allow PUT, PATCH, DELETE, or TRACE
    http_method_names = ['get', 'post', 'head', 'options']

    def _uri_of(self, name):
        return reverse('freemoney:{}'.format(name))

    def _check_and_obtain_page_name(self):
        self._page_index = None
        for index, names in enumerate(WizardPageView.PAGES):
            short_name, long_name = names
            if type(self).page_name == short_name:
                self._page_index = index
                break
        if self._page_index == None:
            raise KeyError('invalid page name: {}'.format(page_name))
        else:
            self.page_name = WizardPageView.PAGES[self._page_index][0]

    def _error_response_unless_applicant(self):
        try:
            self.applicant = self.request.user.applicantprofile
            if applicantprofile.must_change_password:
                # TODO: forced password change
                return server_error(self.request)
            else:
                return None   # success!
        except ObjectDoesNotExist:
            # TODO: make a landing page for non-applicant users
            return server_error(self.request)

    def _ensure_application(self):
        self.application = None
        if 'application' in self.request.session:
            self.application = Application.objects.get(
                    pk=self.request.session['application']
            )
        else:
            candidate_app_iter = Application.objects.filter(
                    applicant=self.request.user.applicantprofile,
            ).iterator()
            for candidate_app in candidate_app_iter:
                if (Semester(candidate_app.due_by) ==
                    Semester(settings.FREEMONEY_DUE_DATE)):
                    if candidate_app.submitted:
                        # TODO: handle gracefully
                        return server_error(self.request)
                    else:
                        self.application = candidate_app
                        break
            if self.application == None:
                if datetime.now(timezone.utc) < settings.FREEMONEY_DUE_DATE:
                    self.application = Application.objects.create(
                            due_at=settings.FREEMONEY_DUE_DATE,
                            applicant=self.request.user.applicantprofile
                    )
                    self.request.session['application'] = self.application.pk
                else:
                    # TODO: handle more gracefully
                    return server_error(self.request)

    def _calculate_valid_buttons(self):
        buttons = [('restart', None)]
        if self._page_index > 0:
            prev_page = WizardPageView.PAGES[self._page_index - 1]
            buttons.append(('prev', prev_page))
        if self._page_index + 1 < len(WizardPageView.PAGES):
            next_page = WizardPageView.PAGES[self._page_index + 1]
            buttons.append(('next', next_page))
        elif self._page_index + 1 == len(WizardPageView.PAGES):
            buttons.append(('submit', None))
        return buttons

    def get(self, request):
        """Don't override this method, but use the hooks instead"""

        if type(self) == WizardPageView:
            raise NotImplementedError('WizardPageView is an abstract base')

        result = self._check_and_obtain_page_name()
        if isinstance(result, HttpResponse):
            return result

        self.request = request

        result = self._error_response_unless_applicant()
        if isinstance(result, HttpResponse):
            return result

        result = self._ensure_application()
        if isinstance(result, HttpResponse):
            return result

        result = self.hook_check_can_access()
        if isinstance(result, HttpResponse):
            return result
        elif result == False:
            previous_page = self._page_index - 1
            if previous_page < 0:
                raise ValueError('first page cannot restrict access')
            else:
                short_name, long_name = WizardPageView.PAGES[previous_page]
                messages.add_message(
                        self.request,
                        messages.ERROR,
                        'Please complete all sections prior to ' + long_name
                )
                return redirect(_url_of(short_name))

        for message in messages.get_messages():
            if message.level == message.ERROR:
                self.show_errors = True

        self.context = {
                'steps': [],
                'postback': self._uri_of(self.page_name),
                'buttons': [x[0] for x in self._calculate_valid_buttons()],
        }
        for short_name, long_name in WizardPageView.PAGES:
            is_active = (short_name == self._page_name)
            self.context['steps'].append((long_name, is_active))

        result = self.hook_prepare_context()
        if isinstance(result, HttpResponse):
            return result

        return render(self.request,
                      self.page_name + '.html',
                      context=self.context)

    def post(self, request):
        """Don't override this method, but use the hooks instead"""

        if type(self) == WizardPageView:
            raise NotImplementedError('WizardPageView is an abstract base')

        result = self._check_and_obtain_page_name()
        if isinstance(result, HttpResponse):
            return result

        self.request = request

        result = self._error_response_unless_applicant()
        if isinstance(result, HttpResponse):
            return result

        result = self._ensure_application()
        if isinstance(result, HttpResponse):
            return result

        result = self.hook_check_can_access()
        if isinstance(result, HttpResponse):
            return result
        elif result == False:
            previous_page = self._page_index - 1
            if previous_page < 0:
                raise ValueError('first page cannot restrict access')
            else:
                short_name, long_name = WizardPageView.PAGES[previous_page]
                messages.add_message(
                        self.request,
                        messages.ERROR,
                        'Please complete all sections prior to ' + long_name
                )
                return redirect(_url_of(short_name))

        result = self.hook_save_changes()
        if isinstance(result, HttpResponse):
            return result

        button_map = {x: y for (x, y) in self._calculate_valid_buttons()}
        self.context = {
                'steps': [],
                'postback': self._uri_of(self.page_name),
                'buttons': button_map.keys()
        }
        for short_name, long_name in WizardPageView.PAGES:
            is_active = (short_name == self._page_name)
            self.context['steps'].append((long_name, is_active))
        submit_type = request.POST.get('submit-type', default=None)

        if submit_type not in button_map:
            messages.add_message(
                    self.request,
                    messages.WARNING,
                    'Unexpected submit-type, but changes on this page are OK'
            )
            return redirect(self._url_to(self.page_name))

        elif submit_type == 'restart':
            self.application.delete()
            del self.request.session['application']
            messages.add_message(self.request, messages.INFO,
                                 'Application was successfully restarted')
            return redirect(self._uri_of(WizardPageView.PAGES[0][0]))

        elif submit_type == 'prev':
            prev_page = WizardPageView.PAGES[self._page_index - 1]
            return redirect(self._url_of(prev_page[0]))

        elif submit_type == 'next':
            result = self.hook_check_can_proceed()
            if isinstance(result, HttpResponse):
                return result
            elif result == False:
                messages.add_message(
                        self.request,
                        messages.ERROR,
                        'Please fix form errors below before proceeding'
                )
                return redirect(self._url_to(self.page_name))
            else:
                next_page = WizardPageView.PAGES[self._page_index + 1]
                return redirect(self._url_of(next_page[0]))

        elif submit_type == 'submit':
            result = self.hook_check_can_proceed()
            if isinstance(result, HttpResponse):
                return result
            elif result == False:
                messages.add_message(
                        self.request,
                        messages.ERROR,
                        'Please fix form errors below before proceeding'
                )
                return redirect(self._url_to(self.page_name))
            else:
                self.application.submitted = True
                self.application.save()
                # TODO: go to a "finished" page
                return server_error(self.request)

    def hook_check_can_access(self):
        """Check whether enough progress has been made to access this page.

        As with all hooks, you may return None to proceed or an HttpResponse
        to suspend normal procedure and immediately send that response. The
        special return value True indicates that all prerequisite application
        fields have been filled and it is safe to access this page.

        Returning None is equivalent to returning True.
        """
        pass

    def hook_save_changes(self):
        """(POST only) Use POSTDATA to modify the Application / DB.

        As with all hooks, you may return None to proceed or an HttpResponse
        to suspend normal procedure and immediately send that response.
        """
        pass

    def hook_check_can_proceed(self):
        """(POST only) Given a request for Next or Submit, return True if OK.

        As with all hooks, you may return None to proceed or an HttpResponse
        to suspend normal procedure and immediately send that response. The
        special value True directs the WizardPageView to redirect to the next
        page in the wizard.

        Returning None is equivalent to returning False.
        """
        pass

    def hook_prepare_context(self):
        """Prior to rendering the template, set .context fields as needed.

        As with all hooks, you may return None to proceed or an HttpResponse
        to suspend normal procedure and immediately send that response.
        """
        pass
