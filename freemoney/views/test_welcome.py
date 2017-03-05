from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from freemoney.models import (Application,
                              ApplicantProfile)

class TestWelcomePage(TestCase):
    """Use the welcome page as a means of testing some common functionality"""

    def setUp(self):
        self.test_user = get_user_model().objects.create_user(
                username='test@example.com',
                password='pass1234'
        )
        self.test_profile = ApplicantProfile.objects.create(
                user=self.test_user,
                must_change_password=False
        )

    def test_multiple_logins(self):
        """Test that the same user has the same app across logins"""

        client_a, client_b = Client(), Client()
        client_a.login(username='test@example.com', password='pass1234')
        client_b.login(username='test@example.com', password='pass1234')

        response = client_a.get(reverse('freemoney:welcome'))
        self.assertTemplateUsed(response, 'welcome.html')
        app_id = client_a.session['application']

        response = client_b.get(reverse('freemoney:welcome'))
        self.assertTemplateUsed(response, 'welcome.html')
        self.assertEqual(app_id, client_b.session['application'])

        response = client_a.post(reverse('freemoney:welcome'),
                                 data={'submit-type': 'restart'},
                                 follow=True)
        self.assertTemplateUsed(response, 'welcome.html')
        self.assertNotEqual(app_id, client_a.session['application'])
        app_id = client_a.session['application']

        response = client_b.get(reverse('freemoney:welcome'), follow=True)
        self.assertTemplateUsed(response, 'welcome.html')
        self.assertEqual(app_id, client_b.session['application'])
