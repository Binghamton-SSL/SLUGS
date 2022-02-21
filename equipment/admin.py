from django.contrib import admin
from nested_admin import NestedStackedInline, NestedModelAdmin, NestedTabularInline
from equipment.models import System, BrokenEquipmentReport, SystemAddon, Equipment, Category, ServiceRecord, Item, SystemQuantity, SystemQuantityAddon
from finance.admin import SystemAddonPricingInline, SystemPricingInline


# Register your models here.
class ServiceRecordInline(NestedStackedInline):
    model = ServiceRecord
    readonly_fields = ['date_created', 'date_last_modified']
    extra = 0


class ItemThroughInline(NestedStackedInline):
    verbose_name = "Child"
    verbose_name_plural = "Children"
    model = Item.children.through
    fk_name = "parent"
    extra = 0


class ItemInline(NestedStackedInline):
    model = Item
    inlines = [ItemThroughInline]
    extra = 0


class EquipmentInline(admin.StackedInline):
    model = SystemQuantity
    extra = 0


class EquipmentAddonInline(admin.StackedInline):
    model = SystemQuantityAddon
    extra = 0


@admin.register(SystemAddon)
class SystemAddonAdmin(admin.ModelAdmin):
    inlines = [SystemAddonPricingInline, EquipmentAddonInline]
    search_fields = ["name"]


@admin.register(System)
class SystemAdmin(admin.ModelAdmin):
    inlines = [SystemPricingInline, EquipmentInline]
    search_fields = ["name"]


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
class EquipmentAdmin(NestedModelAdmin):
    inlines = [ItemInline]
    search_fields = ["name", "brand", "model_number", "reorder_link"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ["name"]


@admin.register(ServiceRecord)
class ServiceRecordAdmin(admin.ModelAdmin):
    verbose_name = "Service Record / Equipment Note"
    verbose_name_plural = "Service Records & Equipment Notes"
    search_fields = ["name", "date_created"]


@admin.register(Item)
class ItemAdmin(NestedModelAdmin):
    inlines = [ServiceRecordInline, ItemThroughInline]
    exclude = ["children"]
    search_fields = ["pk", "barcode", "serial_no"]
