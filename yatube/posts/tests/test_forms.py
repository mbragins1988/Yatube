import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа2',
            slug='test-slug2',
            description='Тестовое описание2',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create_user(username='username')
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author_client = Client()
        self.authorized_author_client.force_login(self.post.author)

        self.image = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.URL_INDEX = ('posts:index', None)
        self.URL_DETAIL = ('posts:post_detail', (self.post.id,))
        self.URL_GROUP = ('posts:group_list', (self.group.slug,))
        self.POST_EDIT_URL = ('posts:post_edit', (self.post.id,))
        self.CTEATE_URL = ('posts:post_create', None)
        self.URL_PROFILE = ('posts:profile', (self.user.username,))
        self.URL_COMMENT = ('posts:add_comment', (self.post.id,))

    def test_create_post(self):
        """Проверка создания нового поста."""
        uploaded = SimpleUploadedFile(
            name="image_1.gif",
            content=self.image,
            content_type="image/gif",
        )
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост формы',
            'group': self.group2.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse(self.CTEATE_URL[0]),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse('posts:profile', args=(self.user,))
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        post = Post.objects.first()
        self.assertIn(
            form_data['image'].name, post.image.name
        )
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.author, self.user)

    def test_post_edit_auth(self):
        """Проверка изменения поста автором"""
        uploaded = SimpleUploadedFile(
            name="image_2.gif",
            content=self.image,
            content_type="image/gif",
        )
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост измененный',
            'group': self.group2.id,
            'image': uploaded,
        }
        response = self.authorized_author_client.post(
            reverse(self.POST_EDIT_URL[0], args=self.POST_EDIT_URL[1]),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                self.URL_DETAIL[0], args=self.URL_DETAIL[1]
            )
        )
        post = Post.objects.first()
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(response.context['post'].text, form_data['text'])
        self.assertEqual(response.context['post'].group.id, form_data['group'])
        self.assertEqual(post.author, self.post.author)
        self.assertIn(
            form_data['image'].name, post.image.name
        )

    def test_post_edit_guest(self):
        """Проверка изменения поста
         неавторизированным пользователем."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост измененный',
            'group': self.group2.id,
        }
        response = self.guest_client.post(
            reverse(self.POST_EDIT_URL[0], args=self.POST_EDIT_URL[1]),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertRedirects(
            response, '/auth/login/?next=/posts/1/edit/'
        )

    def test_add_comment_user(self):
        """Комментировать посты может только авторизованный пользователь"""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Текст комментария',
        }
        response = self.authorized_author_client.post(
            reverse(self.URL_COMMENT[0], args=self.URL_COMMENT[1]),
            data=form_data,
            follow=True
        )
        comment = Comment.objects.first()
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertEqual(self.post.author, self.post.author)
        self.assertEqual(comment.text, form_data['text'])
        self.assertRedirects(
            response, reverse(
                self.URL_DETAIL[0], args=self.URL_DETAIL[1]
            )
        )

    def test_add_comment_not_user(self):
        """Неавторизированный пользователь не может комментировать"""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Текст комментария',
        }
        response = self.guest_client.post(
            reverse(self.URL_COMMENT[0], args=self.URL_COMMENT[1]),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count)
        self.assertRedirects(
            response, '/auth/login/?next=/posts/1/comment/'
        )
