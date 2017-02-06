from django.forms import ModelForm
from django.shortcuts import render
from fm_apply.models import ApplicantResponse


class ApplicantResponseForm(ModelForm):
    class Meta:
        model = ApplicantResponse
        fields = ['name', 'address', 'phone', 'psu_email', 'preferred_email',
                  'psu_id', 'semester_initiated', 'semester_graduating',
                  'cumulative_gpa', 'semester_gpa', 'in_state_tuition']


# Create your views here.
def test(request):
    myform = ApplicantResponseForm()
    return render(request, 'test.html', {'form': myform})
