from django import template
from django.contrib.auth.models import Group

register = template.Library()


@register.filter
def has_group(user, group_name):
    try:
        group = Group.objects.get(name=group_name)
    except Exception:
        return False
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
        if show_notification(user, notification):
            return True
    return False


@register.filter
def isEngineer(job):
    if job is False:
        return False
    return True if "engineer" in str(job.position).lower() else False
