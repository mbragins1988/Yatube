from django import forms
from django.conf import settings
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import PostForm
from ..models import Follow, Group, Post, User


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.URL_INDEX = ('posts:index', None)
        self.URL_DETAIL = ('posts:post_detail', (self.post.id,))
        self.URL_GROUP = ('posts:group_list', (self.group.slug,))
        self.POST_EDIT_URL = ('posts:post_edit', (self.post.id,))
        self.CTEATE_URL = ('posts:post_create', None)
        self.URL_PROFILE = ('posts:profile', (self.user.username,))

        cache.clear()

    def check_post(self, post):
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.group, self.post.group)
        self.assertEqual(post.image, self.post.image)

    def test_about_pages_uses_correct_template(self):
        """При запросе к index, group_list, profile,
        post_detail, post_edit, post_create
        применяются соответствующие шаблоны"""

        templates_pages_names = (
            self.URL_INDEX + ('posts/index.html',),
            self.URL_GROUP + ('posts/group_list.html',),
            self.URL_PROFILE + ('posts/profile.html',),
            self.URL_DETAIL + ('posts/post_detail.html',),
            self.POST_EDIT_URL + ('posts/create_post.html',),
            self.CTEATE_URL + ('posts/create_post.html',),
        )
        for reverse_name, args, template in templates_pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(
                    reverse(reverse_name, args=args)
                )
                self.assertTemplateUsed(response, template)

    def test_post_edit_and_post_create_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        urls = (
            self.CTEATE_URL,
            self.POST_EDIT_URL
        )
        for url, args in urls:
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    response = self.authorized_client.get(
                        reverse(url, args=args)
                    )
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)
                    self.assertIsInstance(
                        response.context.get('form'), PostForm
                    )
                    is_edit_on_page = bool(response.context.get('is_edit'))
                    is_edit_expected = bool(url == 'posts:post_edit')
                    self.assertEqual(is_edit_on_page, is_edit_expected)

    def test_post_pages_show_correct_context(self):
        """Страницы создаются с  верным контекст"""
        urls = (
            self.URL_INDEX,
            self.URL_GROUP,
            self.URL_PROFILE,
            self.URL_DETAIL,
        )
        for url, args in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(reverse(url, args=args))
                if ("page_obj" in response.context):
                    post = response.context.get("page_obj")[0]
                else:
                    post = response.context.get("post")
                self.check_post(post)

    def test_group_page_show_correct_context(self):
        group = self.authorized_client.get(
            reverse(self.URL_GROUP[0], args=self.URL_GROUP[1])
        ).context.get('group')
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.slug, self.group.slug),
        self.assertEqual(group.description, self.group.description)

    def test_profile_page_show_correct_context(self):
        author = self.authorized_client.get(
            reverse(self.URL_PROFILE[0], args=self.URL_PROFILE[1])
        ).context.get(
            'author'
        )
        self.assertEqual(author.username, self.user.username)
        self.assertEqual(author.id, self.user.id)

    def test_index_page_cache(self):
        response1 = self.authorized_client.get(reverse(self.URL_INDEX[0]))
        Post.objects.all().delete()
        response2 = self.authorized_client.get(reverse(self.URL_INDEX[0]))
        self.assertEqual(response1.content, response2.content)
        cache.clear()
        response_clear_cache = self.authorized_client.get(
            reverse(self.URL_INDEX[0])
        )
        self.assertNotEqual(response1, response_clear_cache)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(
            username='auth',
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание группы',
        )
        for i in range(settings.TOTAL_NUMBER_OF_POSTS_IN_PAGINATOR):
            Post.objects.create(
                text=f'Тестовый пост {i}',
                author=cls.author,
                group=cls.group
            )

    def setUp(self):
        self.user = User.objects.create(username='user')
        self.authorized_user = Client()
        self.authorized_user.force_login(self.user)

        self.URL_INDEX = ('posts:index', None)
        self.URL_GROUP = ('posts:group_list', (self.group.slug,))
        self.URL_PROFILE = ('posts:profile', (self.author,))
        self.URL_FOLLOWER = ('posts:follow_index', None)

        self.authorized_user.get(
            reverse(
                'posts:profile_follow',
                args=(self.author,)
            )
        )

    def test_paginator_on_pages(self):
        """Проверка пагинатора на двух страницах
        десять записей на странице."""
        urls = (
            self.URL_INDEX,
            self.URL_GROUP,
            self.URL_PROFILE,
            self.URL_FOLLOWER,
        )
        pages = (
            ('?page=1', settings.NUMBER__OF_POSTS),
            ('?page=2', settings.TOTAL_NUMBER_OF_POSTS_IN_PAGINATOR
             - settings.NUMBER__OF_POSTS)
        )
        for url, args in urls:
            with self.subTest(url=url):
                for page, nums in pages:
                    with self.subTest(page=page):
                        response = self.authorized_user.get(
                            reverse(url, args=args) + page
                        )
                        self.assertEqual(
                            len(response.context['page_obj']),
                            nums
                        )


class FollowersTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тест подписки',
        )

    def setUp(self):
        self.user = User.objects.create_user(username='user')
        self.authorized_user = Client()
        self.authorized_user.force_login(self.user)
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)

    def test_subscription_(self):
        """Проверка работы подписки"""
        count_1 = Follow.objects.count()
        self.authorized_user.get(
            reverse(
                'posts:profile_follow',
                args=(self.author,)
            )
        )
        count_2 = Follow.objects.count()
        self.assertEqual(count_2, count_1 + 1)
        follow = Follow.objects.first()
        self.assertEqual(follow.author, self.post.author)
        self.assertEqual(follow.user, self.user)

    def test_unsubscription(self):
        """Проверка работы отписки"""
        Follow.objects.create(
            author=self.author,
            user=self.user,
        )
        count_1 = Follow.objects.count()
        self.authorized_user.get(
            reverse(
                'posts:profile_unfollow',
                args=(self.author,)
            )
        )
        count_2 = Follow.objects.count()
        self.assertEqual(count_2, count_1 - 1)

    def test_cant_follow_myself(self):
        """Невозможно подписаться на себя"""
        count_1 = Follow.objects.count()
        self.authorized_author.get(
            reverse(
                'posts:profile_unfollow',
                args=(self.author,)
            )
        )
        count_2 = Follow.objects.count()
        self.assertEqual(count_1, count_2)

    def test_second_time_follow_impossible(self):
        """Невозможно подписаться на автора несколько раз"""
        count_1 = Follow.objects.count()
        subscription = self.authorized_user.get(
            reverse(
                'posts:profile_follow',
                args=(self.author,)
            )
        )
        for _ in range(settings.NUMBER_OF_SUBSCRIPTIONS):
            subscription
        count_2 = Follow.objects.count()
        self.assertEqual(count_2, count_1 + 1)
