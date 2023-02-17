from django.contrib import admin
from nested_admin import NestedStackedInline, NestedModelAdmin, NestedTabularInline
from import_export.admin import ImportExportMixin
from import_export import resources
from equipment.models import (
    System,
    BrokenEquipmentReport,
    SystemAddon,
    Equipment,
    Category,
    ServiceRecord,
    Item,
    SystemQuantity,
    SystemQuantityAddon,
    Vendor,
    VendorEquipment,
)
from finance.admin import SystemAddonPricingInline, SystemPricingInline, VendorEquipmentPricingInline


# Register your models here.
class ServiceRecordInline(NestedStackedInline):
    model = ServiceRecord
    readonly_fields = ["date_created", "date_last_modified"]
    extra = 0


class ItemThroughInline(NestedStackedInline):
    verbose_name = "Child"
    verbose_name_plural = "Children"
    model = Item.children.through
    fk_name = "parent"
    extra = 0
    autocomplete_fields = ["child"]


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

class VendorEquipmentInline(admin.StackedInline):
    model = VendorEquipment
    extra = 0
    search_fields = ["name"]


@admin.register(SystemAddon)
class SystemAddonAdmin(admin.ModelAdmin):
    inlines = [SystemAddonPricingInline, EquipmentAddonInline]
    search_fields = ["name"]


@admin.register(System)
class SystemAdmin(admin.ModelAdmin):
    inlines = [SystemPricingInline, EquipmentInline]
    ordering = ["department", "name"]
    search_fields = ["name"]


@admin.register(BrokenEquipmentReport)
class BrokenEquipmentReportAdmin(admin.ModelAdmin):
    autocomplete_fields = ["reported_broken_by", "broken_system"]
    list_filter = ["status", "broken_system"]
    list_display = ("__str__", "date_filed")
    readonly_fields = ["date_filed"]
    ordering = ["date_filed"]
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
    list_filter = ["category", "brand", "department"]
    search_fields = ["name", "brand", "model_number", "reorder_link"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ["name"]


@admin.register(ServiceRecord)
class ServiceRecordAdmin(admin.ModelAdmin):
    search_fields = ["name", "date_created"]
    autocomplete_fields = ["item"]


class ItemResource(resources.ModelResource):
    class Meta:
        model = Item
        fields = (
            "id",
            "status",
            "label",
            "serial_no",
            "purchase_date",
            "item_type__name",
            "item_type__description",
            "item_type__brand",
            "item_type__model_number",
            "item_type__name",
            "item_type__department",
            "item_type__value",
            "item_type__wattage",
            "item_type__category",
            "barcode",
            "children",
            "last_updated",
        )


@admin.register(Item)
class ItemAdmin(ImportExportMixin, NestedModelAdmin):
    resource_class = ItemResource
    inlines = [ServiceRecordInline, ItemThroughInline]
    # list_filter = ["equipment__department"]
    exclude = ["children"]
    search_fields = ["pk", "barcode", "serial_no", "item_type__name", "item_type__brand", "item_type__model_number"]

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    search_fields = ["name", "phone_number", "email", "website"]

@admin.register(VendorEquipment)
class VendorEquipmentAdmin(admin.ModelAdmin):
    inlines = [VendorEquipmentPricingInline]
    autocomplete_fields = ["vendor"]
    search_fields = ["vendor__name", "name", "description"]