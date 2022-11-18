from django.contrib import admin
from .models import Notification, signupStatus, onboardingStatus, Attachment
from nested_admin import NestedGenericTabularInline

# Register your models here.
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    filter_horizontal = ("groups_to_send_to",)


@admin.register(signupStatus)
class signupStatus(admin.ModelAdmin):
    pass


@admin.register(onboardingStatus)
class onboardingStatusAdmin(admin.ModelAdmin):
    pass


class AttachmentInlineAdmin(NestedGenericTabularInline):
    model = Attachment
    extra = 0