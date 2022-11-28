from django import template

register = template.Library()


@register.filter
def addclass(field, css):
    field.field.widget.attrs['class'] = css
    return field


@register.filter
def add_placeholder(field, placeholder=None):
    field.field.widget.attrs['placeholder'] = (
        placeholder if placeholder is not None else field.field.help_text
    )
    return field
