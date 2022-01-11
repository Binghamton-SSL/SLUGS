from django.contrib import admin
from django.db.models.lookups import EndsWith
from equipment.models import System, BrokenEquipmentReport, SystemAddon, Equipment, Category, ServiceRecord, Item, SystemQuantity, SystemQuantityAddon
from finance.admin import SystemAddonPricingInline, SystemPricingInline


# Register your models here.
class ItemInline(admin.StackedInline):
    model = Item
    extra = 0


class EquipmentInline(admin.StackedInline):
    model = SystemQuantity
    extra = 0


class EquipmentAddonInline(admin.StackedInline):
    model = SystemQuantityAddon
    extra = 0


@admin.register(SystemAddon)
class SystemAddon(admin.ModelAdmin):
    inlines = [SystemAddonPricingInline, EquipmentAddonInline]
    search_fields = ["name"]
    pass


@admin.register(System)
class SystemAdmin(admin.ModelAdmin):
    inlines = [SystemPricingInline, EquipmentInline]
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


@admin.register(Equipment)
class Equipment(admin.ModelAdmin):
    inlines = [ItemInline]
    search_fields = ["name"]
    pass


@admin.register(Category)
class Category(admin.ModelAdmin):
    search_fields = ["name"]
    pass


@admin.register(ServiceRecord)
class ServiceRecord(admin.ModelAdmin):
    inlines = [ItemInline]
    search_fields = ["name"]
    pass


@admin.register(Item)
class Item(admin.ModelAdmin):
    search_fields = ["id"]
    pass


@admin.register(SystemQuantity)
class SystemQuantity(admin.ModelAdmin):
    search_fields = ["system"]
    pass
