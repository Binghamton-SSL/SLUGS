from django.contrib import admin
import nested_admin
from django.contrib.contenttypes.admin import GenericStackedInline
from django.urls import path
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from .models import *
from employee.models import Employee as EmployeeObject
from .forms import SelectEmployeesForm

# Register your models here.
class ShiftInline(GenericStackedInline, nested_admin.NestedStackedInline):
    model = Shift
    inlines=[]
    extra = 0
    readonly_fields = ['total_hours']

class SystemInstanceInline(nested_admin.NestedStackedInline):
    # autocomplete_fields = ['system']
    model = SystemInstance
    extra = 1

class EmployeeInline(nested_admin.NestedStackedInline):
    autocomplete_fields = ['linked_employee']
    inlines = [ShiftInline]
    model = Employee
    extra = 1

    def get_fields(self, request, obj=None):
        fields = super(EmployeeInline, self).get_fields(request, obj)
        fields.remove('linked_system')
        return fields

# class EngineerInline(nested_admin.NestedStackedInline):
#     inlines = [ShiftInline]
#     model = Engineer
#     extra = 1

# class TechInline(nested_admin.NestedStackedInline):
#     inlines = [ShiftInline]
#     model = Tech
#     extra = 0

# class LoadInline(nested_admin.NestedStackedInline):
#     inlines = [ShiftInline]
#     model = Load
#     extra = 0

# class ProbieInline(nested_admin.NestedStackedInline):
#     inlines = [ShiftInline]
#     model = Probie
#     extra = 0

class GigAdmin(nested_admin.NestedModelAdmin):
    inlines = [SystemInstanceInline, EmployeeInline]
    list_filter = ('archived','start','location',)
    search_fields = ('org','name','location__name',)
    list_display = ('__str__','get_assign_link',)   
    # readonly_fields = ('status',)

    def assign_view(self, request,object_id):
        obj = Gig.objects.get(pk=object_id)
        open_positions = Employee.objects.filter(linked_gig=obj).filter(linked_employee=None)
        for pos in open_positions:
            pos.interested_employees = InterestedEmployee.objects.filter(job=pos)
            if request.method == 'POST':
                for item in list(request.POST.dict().keys()):
                    if item != "csrfmiddlewaretoken":
                        emp_obj = Employee.objects.get(id=item[0])
                        emp_obj.linked_employee = EmployeeObject.objects.get(id=request.POST.get(item)) if (request.POST.get(item) != "") else None
                        emp_obj.save()
                return redirect('admin:gig_gig_changelist')
            else: 
                pos.form = SelectEmployeesForm(instance=pos, prefix=pos.id, interested_employees=pos.interested_employees)
        context = dict(
           # Include common variables for rendering the admin template.
           self.admin_site.each_context(request),
           # Anything else you want in the context...
           object_id=object_id,
           object= obj,
           title="Assign Work",
           open_positions = open_positions
        )
        return TemplateResponse(request, "gig/assign.html", context)

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('<path:object_id>/assign/', self.assign_view, name='gig_gig_assign'),
        ]
        return my_urls + urls

class LocationAdmin(admin.ModelAdmin):
    pass;
class OrganizationAdmin(admin.ModelAdmin):
    pass;
class ContactAdmin(admin.ModelAdmin):
    pass;
class SystemAdmin(nested_admin.NestedModelAdmin):
    search_fields = ['name']
    inlines = [EmployeeInline]
    pass;
class BrokenEquipmentAdmin(admin.ModelAdmin):
    readonly_fields = ['date_filed']
    list_filter = ('status','date_filed')
    fieldsets = [(None, {'fields': ('broken_system', 'date_filed',)}),
        ('Reported Info', {'fields': ('reported_broken_by','notes')}),
        ('Technician Use Only', {'fields': ('status','investigation')}),]
    pass;
class SignupAdmin(admin.ModelAdmin):
    pass;
class EmployeeAdmin(admin.ModelAdmin):
    list_filter = ('not_associated_with_event',)

admin.site.register(Gig, GigAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(Organization, OrganizationAdmin)
admin.site.register(System, SystemAdmin)
admin.site.register(Signup, SignupAdmin)
admin.site.register(InterestedEmployee, admin.ModelAdmin)
admin.site.register(Shift, admin.ModelAdmin)
admin.site.register(Employee, EmployeeAdmin)
admin.site.register(Contact, ContactAdmin)
admin.site.register(BrokenEquipmentReport, BrokenEquipmentAdmin)