from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse


class StaticPagesURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_url_exists_at_desired_location(self):
        """Проверка доступности адреса /about/author и /about/tech."""
        availability_url = {
            '/about/author/': HTTPStatus.OK.value,
            '/about/tech/': HTTPStatus.OK.value
        }
        for url, status in availability_url.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, status)

    def test_about_url_uses_correct_template(self):
        """Проверка шаблона для адреса /about/author/ и /about/tech."""
        availability_template = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html'
        }
        for url, template in availability_template.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_about_pages_uses_correct_template(self):
        """При запросе к about:author и about:tech
        применяются шаблоны about/author.html и about/tech.html"""

        templates_pages_names = {
            'about/author.html': reverse('about:author'),
            'about/tech.html': reverse('about:tech')
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
