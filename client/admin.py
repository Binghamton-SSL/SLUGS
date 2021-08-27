from django.contrib import admin
from client.models import OrgContact, Organization


# Register your models here.
@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    search_fields = ["name", "SA_account_num"]


@admin.register(OrgContact)
class OrgContactAdmin(admin.ModelAdmin):
    search_fields = ["name", "organization__name"]
    autocomplete_fields = ["organization"]
