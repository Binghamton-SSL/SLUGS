from django.contrib import admin
from equipment.models import System, BrokenEquipmentReport, SystemAddon


@admin.register(SystemAddon)
class SystemAddon(admin.ModelAdmin):
    search_fields = ["name"]
    pass


# Register your models here.
@admin.register(System)
class SystemAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    pass


@admin.register(BrokenEquipmentReport)
class BrokenEquipmentReportAdmin(admin.ModelAdmin):
    autocomplete_fields = ["reported_broken_by", "broken_system"]
    list_filter = ["status", "broken_system"]
    readonly_fields = ["date_filed"]
    fieldsets = [
        (None, {"fields": ("status",)}),
        (
            "Report",
            {"fields": ("date_filed", "reported_broken_by", "broken_system", "notes")},
        ),
        (None, {"fields": ("investigation",)}),
    ]
