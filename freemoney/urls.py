from django.conf.urls import url
import freemoney.views
import freemoney.views.dummy   # TODO: remove

app_name = 'freemoney'
urlpatterns = [
        url(r'^welcome$', freemoney.views.WelcomePage.as_view(),
                          name='welcome'),
        url(r'^award$', freemoney.views.AwardPage.as_view(),
                         name='award'),
        url(r'^basicinfo$', freemoney.views.BasicInfoPage.as_view(),
                            name='basicinfo'),
#        url(r'^finaid$', freemoney.views.FinancialAidPage.as_view(),
#                         name='finaid'),
        url(r'^dummy$', freemoney.views.dummy.DummyPage.as_view(),
                        name='dummy')   # TODO: remove
]
