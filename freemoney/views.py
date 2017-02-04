from django.shortcuts import render
from django import forms

class TestForm(forms.Form):
    your_name = forms.CharField(label='Your name', max_length=100)

# Create your views here.
def test(request):
    return render(request, 'test.html', {'form': TestForm()})
