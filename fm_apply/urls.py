from django.conf.urls import url
import fm_apply.views

app_name = 'fm_apply'
urlpatterns = [
        url(r'^welcome$', fm_apply.views.wizard_welcome,
                          name='welcome'),
        url(r'^awards$', fm_apply.views.wizard_awards,
                         name='awards'),
       #url(r'^feedback$', fm_apply.views.wizard_feedback, 
                          # name='feedback'),
]
