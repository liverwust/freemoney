from django.conf.urls import url
import freemoney.views
import freemoney.views.dummy   # TODO: remove

app_name = 'freemoney'
urlpatterns = [
        url(r'^welcome$', freemoney.views.WelcomePage.as_view(),
                          name='welcome'),
        url(r'^awards$', freemoney.views.AwardsPage.as_view(),
                         name='awards'),
        url(r'^feedback$', freemoney.views.FeedbackPage.as_view(),
                           name='feedback'),
        url(r'^dummy$', freemoney.views.dummy.DummyPage.as_view(),
                        name='dummy')   # TODO: remove
]
