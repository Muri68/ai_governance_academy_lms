from django import template
from apps.accounts.utils import get_country_flag, get_country_name, split_phone

register = template.Library()


@register.filter
def country_flag(phone):
    return get_country_flag(phone)


@register.filter
def country_name(phone):
    return get_country_name(phone)


@register.filter
def phone_parts(phone):
    """Returns dict {'cc': '+44', 'national': '7911123456'}"""
    cc, national = split_phone(phone)
    return {'cc': cc, 'national': national}