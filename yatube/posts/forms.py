from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].widget.attrs['placeholder'] = (
            'Напишите пост'
        )
        self.fields['group'].empty_label = (
            'Выберите группу'
        )

    def clean_text(self):
        text = self.cleaned_data['text']
        if 'блин' in text.lower():
            raise forms.ValidationError('Нельзя применять слово "блин"')
        return text

    class Meta:
        model = Post
        fields = ('group', 'text', 'image')
        labels = {
            'text': "Текст поста",
            'group': "Группа",
        }
        help_texts = {
            'text': "Текст нового поста",
            'group': "Группа, к которой будет относиться пост",
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
