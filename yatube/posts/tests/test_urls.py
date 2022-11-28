from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Group, Post, User


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='authtor')
        cls.group = Group.objects.create(
            title='title_test',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='user')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author = Client()
        self.authorized_author.force_login(self.post.author)

        self.URL_INDEX = ('/')
        self.URL_DETAIL = (f'/posts/{self.post.id}/')
        self.URL_GROUP = (f'/group/{self.group.slug}/')
        self.POST_EDIT_URL = (f'/posts/{self.post.id}/edit/')
        self.CTEATE_URL = ('/create/')
        self.URL_PROFILE = (f'/profile/{self.user.username}/')

        self.urls_templates_guest_client = {
            self.URL_INDEX: 'posts/index.html',
            self.URL_GROUP: 'posts/group_list.html',
            self.URL_PROFILE: 'posts/profile.html',
            self.URL_DETAIL: 'posts/post_detail.html',
        }

        self.urls_templates_authorized_client = {
            self.CTEATE_URL: 'posts/create_post.html',
            self.POST_EDIT_URL: 'posts/create_post.html',
        }

        cache.clear()

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for url, template in (
                *self.urls_templates_guest_client.items(),
                *self.urls_templates_authorized_client.items()
        ):
            with self.subTest(template=template):
                response = self.authorized_author.get(url)
                self.assertTemplateUsed(response, template)

    def test_availability_for_guest_client(self):
        """Проверка доступа страниц для незарегистрированного пользователя."""
        for url in self.urls_templates_guest_client.keys():
            with self.subTest(url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
        for url in self.urls_templates_authorized_client.keys():
            with self.subTest(url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_availability_for_author(self):
        """Проверка доступа страниц для автора."""
        for url in self.urls_templates_authorized_client.keys():
            with self.subTest(url):
                response = self.authorized_author.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_for_authorized_client(self):
        """Зарегистрированный пользователь
        не имеет доступа к редактированию."""
        response = self.authorized_client.get(self.POST_EDIT_URL)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, self.URL_DETAIL)

    def test_create_url_redirect_anonymous_on_auth_login(self):
        """Незарегистрированный пользователь
        не имеет доступа к созданию поста."""
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_unexisting_page_at_desired_location(self):
        """Страница /unexisting_page/ не существует."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
