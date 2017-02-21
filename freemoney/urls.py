from django.conf.urls import url
import freemoney.views

app_name = 'freemoney'
urlpatterns = [
        url(r'^welcome$', freemoney.views.wizard_welcome,
                          name='welcome'),
        url(r'^awards$', freemoney.views.wizard_awards,
                         name='awards'),
       #url(r'^feedback$', fm_apply.views.wizard_feedback, 
                          # name='feedback'),
]
