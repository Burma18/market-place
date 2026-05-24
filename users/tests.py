from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse


class AuthViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.password = 'SecurePass123!'

    def test_register(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'password1': self.password,
            'password2': self.password,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_login(self):
        User.objects.create_user(username='loginuser', password=self.password)
        response = self.client.post(reverse('login'), {
            'username': 'loginuser',
            'password': self.password,
        })
        self.assertEqual(response.status_code, 302)

    def test_login_invalid(self):
        response = self.client.post(reverse('login'), {
            'username': 'nobody',
            'password': 'wrong',
        })
        self.assertEqual(response.status_code, 200)

    def test_logout(self):
        user = User.objects.create_user(username='logoutuser', password=self.password)
        self.client.login(username='logoutuser', password=self.password)
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)
