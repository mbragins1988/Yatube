from http import HTTPStatus

from django.test import Client, TestCase


class StaticPagesURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_auth_url_exists_at_desired_location(self):
        """Проверка доступности адреса auth/signup,
        auth/login/ и auth/logout/."""
        availability_url = {
            '/auth/signup/': HTTPStatus.OK.value,
            '/auth/login/': HTTPStatus.OK.value,
            '/auth/logout/': HTTPStatus.OK.value
        }
        for url, status in availability_url.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, status)

    def test_about_url_uses_correct_template(self):
        """Проверка шаблона для адреса auth/signup,
        auth/login/ и auth/logout/."""
        availability_template = {
            '/auth/signup/': 'users/signup.html',
            '/auth/login/': 'users/login.html',
            '/auth/logout/': 'users/logged_out.html'
        }
        for url, template in availability_template.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
