from django import template

register = template.Library()


@register.filter
def get_hour_value(dict, key):
    if key in dict:
        return dict[key][1]
    else:
        return None

@register.filter
def get_price_at_date(object, date):
    return object.get_price_at_date(date)