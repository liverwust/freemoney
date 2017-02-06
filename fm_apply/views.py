import collections
from django.forms import ModelForm
from django.shortcuts import render


NavItem = collections.namedtuple('NavItem', ['is_active', 'name'])


def default(request):
    return static_wizard(request, 'welcome')


def static_wizard(request, section):
    items = [NavItem(False, 'test1'), NavItem(False, 't2'),
             NavItem(True, 'test3'), NavItem(False, 't4')]
    return render(request,
                  template_name='welcome.html',
                  context={'nav_list': items})
