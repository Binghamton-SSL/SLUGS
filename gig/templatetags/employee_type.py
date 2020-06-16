from django import template
from ..models import Shift

register = template.Library()

@register.filter
def isType(employee, emp_type):
    return True if emp_type == employee.employee_type else False

@register.filter
def numOfType(employees, emp_type):
    return len(employees.filter(employee_type=emp_type))

@register.filter
def hasEmptyEmps(gig):
    return True if gig.employees.filter(linked_employee=None).exists() else False

@register.filter
def isEngineer(user):
    if user == False:
        return False
    return True if "engineer" in str(user.employee_type).lower() else False
