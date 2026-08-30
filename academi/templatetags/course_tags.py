from django import template

register = template.Library()

@register.filter
def is_in_list(value, list):
    """Verifica si un valor está en una lista"""
    return value in list