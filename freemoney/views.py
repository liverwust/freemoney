from django.shortcuts import render
from django import forms

class TestForm(forms.Form):
    your_name = forms.CharField(label='Your name', max_length=100)
    your_int = forms.IntegerField()

# Create your views here.
def test(request):
    myint = 1
    if 'myint' in request.session:
        myint = request.session['myint']
        request.session['myint'] += 1
    else:
        myint = 1
        request.session['myint'] = myint
    myform = TestForm(initial={'your_int': myint})
    return render(request, 'test.html', {'form': myform})
