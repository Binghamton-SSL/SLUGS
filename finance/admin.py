from django.contrib import admin
from .models import *

# Register your models here.
class FeeInline(admin.TabularInline):
    model = Fee
    extra = 0

class InvoiceAdmin(admin.ModelAdmin):
    exclude = ('date_created',)
    filter_horizontal = ('fees',)
    readonly_fields = ['subtotal','total']
    list_filter = ('status','linked_gig__start')
    search_fields = ('linked_gig__name','linked_gig__org__name','status',)

class FeeAdmin(admin.ModelAdmin):
    pass;
    
admin.site.register(Invoice, InvoiceAdmin)
admin.site.register(Fee, FeeAdmin)