from .common import WizardView


class WelcomePage(WizardView):
    """Informational page at the beginning of the application wizard."""

    page_name = 'welcome'
    template_name = 'welcome.html'
