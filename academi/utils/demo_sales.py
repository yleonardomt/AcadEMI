"""Include simulated transactions in demo dashboards, never in real sales reports."""

from django.conf import settings


def visible_sales(queryset, method_field='payment_method'):
    if settings.DEMO_CHECKOUT:
        return queryset
    return queryset.exclude(**{method_field: 'demo'})
