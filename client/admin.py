from django.contrib import admin
from client.models import OrgContact, Organization


# Register your models here.
@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    search_fields = ["name", "SA_account_num"]
    ordering = ["name"]


@admin.register(OrgContact)
class OrgContactAdmin(admin.ModelAdmin):
    search_fields = ["name", "organization__name", "email", "phone_number"]
    autocomplete_fields = ["organization"]
    ordering = ["organization__name", "name"]
