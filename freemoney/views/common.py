from datetime import datetime, timedelta, timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django.views.defaults import server_error
from freemoney.models import Application
from freemoney.utils import Semester


class WizardView(LoginRequiredMixin, View):
    """Class-based view for wizard pages.

    This view provides several advantages over a regular view function:
    * Ensures that the user is logged in as a Django User
    * Ensures that the Django User belongs to the proper group
    * Automatically grabs the Application instance from the session
    * Generates nav "pill" links around the page content
    * Prevents skipping pages which contain validation errors

    Provide the following class attributes:
    * ``page_name``: short name of this page in the wizard (see PAGES)
    * (optional) ``required_fields``: collection of the Application fields
      which must be successfully validated before this page may be accessed
    * (optional) ``template_name``: if provided, no need to override the
      render_page() function

    Override the following instance functions (which can reference the
    .application and .request properties):
    * ``render_page()``: return a rendered response to a GET request
    * ``save_changes()``: handle client data during POST; return False to
      prevent moving off of the current page
    """

    PAGES = [('welcome', 'Welcome'),
             ('awards', 'Choose Awards'),
             ('dummy', 'Dummy Page')] # TODO: get rid of this
             #('awards', 'Choose Awards'),
             #('feedback', 'Peer Feedback')]

    # don't allow PUT, PATCH, or DELETE
    http_method_names = ['get', 'post', 'head', 'options', 'trace']

    def _uri_of(self, name):
        return reverse('freemoney:{}'.format(name))

    def _check_and_obtain_class_attributes(self):
        self._page_index = None
        for index, names in enumerate(WizardView.PAGES):
            short_name, long_name = names
            if type(self).page_name == short_name:
                self._page_index = index
                break
        if self._page_index == None:
            raise KeyError('invalid page name: {}'.format(page_name))
        else:
            self._page_name = WizardView.PAGES[self._page_index][0]

        if hasattr(type(self), 'required_fields'):
            if self._page_index == 0:
                raise ValueError('first page cannot require validation')
            else:
                self._required_fields = set(type(self).required_fields)
        else:
            self._required_fields = set()

        if hasattr(type(self), 'template_name'):
            self._template_name = type(self).template_name
        else:
            self._template_name = None

    def _error_response_unless_applicant(self):
        try:
            applicantprofile = self.request.user.applicantprofile
            if applicantprofile.must_change_password:
                # TODO: forced password change
                return server_error(self.request)
            else:
                return None   # success!
        except ObjectDoesNotExist:
            # TODO: make a landing page for non-applicant users
            return server_error(self.request)

    def _ensure_application(self):
        # TODO: make sure that can be set by an admin
        cycle_due_date = datetime(year=2017, month=4, day=1, 
                                  hour=23, minute=59, second=59,
                                  tzinfo=timezone.utc)

        application = None
        if 'application' in self.request.session:
            application = Application.objects.get(
                    pk=self.request.session['application']
            )
        else:
            application = Application.objects.filter(
                    applicant=self.request.user.applicantprofile
            ).first()
            if application == None:
                if datetime.now(timezone.utc) < cycle_due_date:
                    application = Application.objects.create(
                            due_at=cycle_due_date,
                            applicant=self.request.user.applicantprofile
                    )
                    self.request.session['application'] = application.pk
                else:
                    # TODO: handle more gracefully
                    raise Exception('Too late!')

        potential_dupe_apps = Application.objects.filter(
                applicant=self.request.user.applicantprofile
        )
        for other_app in potential_dupe_apps.iterator():
            if application != other_app:
                if Semester(application.due_at) == Semester(other_app.due_at):
                    # TODO: handle the case of a duplicate application
                    raise Exception('Multiple apps in the system for you')

        if application.submitted:
            # TODO: handle (much) more gracefully
            raise Exception('Already submitted application')

        return application

    def _error_response_unless_validated(self):
        if len(self._required_fields) > 0:
            try:
                self.application.full_clean(force=True)
                return None   # definite success, no validation errors
            except ValidationError as exc:
                for field in self._required_fields:
                    if field in exc.error_dict:
                        last_index = self._page_index - 1
                        last_page = WizardView.PAGES[last_index]
                        return redirect(self._uri_of(last_page[0]))
                return None   # no *relevant* validation errors

    def _calculate_valid_buttons(self):
        buttons = [('cancel', None)]
        if self._page_index > 0:
            prev_page = WizardView.PAGES[self._page_index - 1]
            buttons.append(('prev', prev_page))
        if self._page_index + 1 < len(WizardView.PAGES):
            next_page = WizardView.PAGES[self._page_index + 1]
            buttons.append(('next', next_page))
        elif self._page_index + 1 == len(WizardView.PAGES):
            buttons.append(('submit', None))
        return buttons


    def get(self, request):
        self._check_and_obtain_class_attributes()
        self.request = request
        error_response = self._error_response_unless_applicant()
        if error_response != None:
            return error_response
        self.application = self._ensure_application()
        error_response = self._error_response_unless_validated()
        if error_response != None:
            return error_response

        context = {
                'steps': [],
                'postback': self._uri_of(self._page_name),
                'buttons': [x[0] for x in self._calculate_valid_buttons()],
        }
        for short_name, long_name in WizardView.PAGES:
            uri = self._uri_of(short_name)
            is_active = (short_name == self._page_name)
            is_enabled = True  # TODO: hacked
            context['steps'].append((long_name,
                                     uri,
                                     is_active,
                                     is_enabled))
        return self.render_page(context)

    def post(self, request):
        self._check_and_obtain_class_attributes()
        self.request = request
        error_response = self._error_response_unless_applicant()
        if error_response != None:
            return error_response
        self.application = self._ensure_application()
        error_response = self._error_response_unless_validated()
        if error_response != None:
            return error_response

        submit_type = request.POST.get('submit-type', default=None)
        for button_type, button_page in self._calculate_valid_buttons():
            if submit_type == button_type:
                if submit_type == 'cancel':
                    self.application.delete()
                    del self.request.session['application']
                    # TODO: back to some landing page
                    return redirect(self._uri_of('dummy'))
                elif submit_type == 'submit':
                    if self.save_changes():
                        # TODO: go to a "finished" page
                        return server_error(self.request)
                    else:
                        # TODO: error handling?
                        return redirect(self._uri_of(self._page_name))
                else:
                    if self.save_changes():
                        return redirect(self._uri_of(button_page[0]))
                    else:
                        # TODO: error handling?
                        return redirect(self._uri_of(self._page_name))
        raise ValueError('unrecognized or invalid submit-type')

    def render_page(self, context):
        """Override and return a fully-rendered response object."""
        if self._template_name == None:
            raise ValueError('default renderer must have template_name')
        else:
            return render(self.request, self._template_name, context=context)

    def save_changes(self):
        """Override and return True to proceed or False to stay on page."""
        return True
