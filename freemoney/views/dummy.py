from django.http import HttpResponse
from .common import WizardView


#TODO: remove this entire class!
class DummyPage(WizardView):
    """Dummy to allow testing the wizard w/o a full submission at the end"""
    page_name = 'dummy'

    def render_page(self, context):
        return HttpResponse('<b>DUMMY</b>', content_type='text/html')
