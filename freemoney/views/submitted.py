from django.views.generic.base import TemplateView


class SubmittedPage(TemplateView):
    template_name = "submitted.html"
