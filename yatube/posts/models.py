from core.models import CreatedModel
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    """Создание модели для сообществ.
    Включает в себя название группы,
    уникальный адрес группы, текст,
    описывающий сообщество
    """
    title = models.CharField("Заголовок", max_length=200)
    slug = models.SlugField("Название вкладки", unique=True)
    description = models.TextField("Описание")

    class Meta:
        verbose_name = "Группы"
        verbose_name_plural = "Группы"

    def __str__(self):
        return self.title


class Post(CreatedModel):
    """Создание модели для хранения постов.
    В ней храниться:
    текст поста,
    дата публикации поста,
    автор поста,
    группа
    """
    text = models.TextField(
        'Текст поста',
        help_text='Введите текст поста'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='posts'
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        related_name='posts',
        blank=True,
        null=True,
        verbose_name='Группа',
        help_text='Группа, к которой будет относиться пост'
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        verbose_name = "Посты"
        verbose_name_plural = "Посты"
        ordering = ('-pub_date',)

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    text = models.TextField('Текст', help_text='Текст нового комментария')
    created = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.text


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
        help_text='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following",
        verbose_name='Блогер',
        help_text='На Вас подписаны'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("user", "author"),
                name="unique_pair"
            ),
        ]
