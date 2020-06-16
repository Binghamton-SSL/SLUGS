from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from tinymce.widgets import TinyMCE
from django.db import models


from .forms import UserAdminCreationForm, UserAdminChangeForm
from .models import *

class UserAdmin(BaseUserAdmin):
    def group(self, user):
        groups = []
        for group in user.groups.all():
            groups.append(group.name)
        return ', '.join(groups)
    group.short_description = 'Groups'
    # The forms to add and change user instances
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('__str__', 'group', 'active', 'staff', 'admin')
    list_filter = ('active','staff','admin',)
    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets

        if request.user.is_superuser:
            perm_fields = ('staff', 'active', 'admin',
                           'groups', 'user_permissions')
        else:
            # modify these to suit the fields you want your
            # staff user to be able to edit
            perm_fields = ('active', 'staff','groups')

        return [(None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name','last_name','phone_number','bnum')}),
        ('Permissions', {'fields': perm_fields}),]
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'bnum')}
        ),
    )
    search_fields = ('email','first_name','last_name','bnum')
    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions',)

class NotificationAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.TextField: {'widget': TinyMCE()},
    }
    filter_horizontal = ('groups_to_send_to',)

admin.site.register(Employee, UserAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(NewEmployeesAllowed, admin.ModelAdmin)
admin.site.register(Wage, admin.ModelAdmin)