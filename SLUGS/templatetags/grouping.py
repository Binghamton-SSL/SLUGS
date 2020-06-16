from django import template
from django.contrib.auth.models import Group

register = template.Library()

@register.filter
def has_group(user, group_name):
    group = Group.objects.get(name=group_name)
    return True if group in user.groups.all() else False

@register.filter
def show_notification(user, notification):
    for group in notification.groups_to_send_to.all():
        if group in user.groups.all():
            return True
    return False

@register.filter
def show_notifications(user, notifications):
    for notification in notifications:
        if show_notification(user,notification):
            return True
    return False