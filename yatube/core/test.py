from django.test import Client, TestCase


class CoreTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_page_404_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        response = self.guest_client.get('/non-page/')
        self.assertTemplateUsed(response, 'core/404.html')
