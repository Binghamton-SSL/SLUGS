from django import template


register = template.Library()


@register.inclusion_tag("finance/components/auto_sign.html")
def autosign():
    return locals()