from training.models import Trainee
from gig.models import Job
from finance.models import Shift
from employee.models import OfficeHours


def getShiftsForEmployee(emp):
    shifts = Shift.objects.none()
    # Training
    for trainee in Trainee.objects.filter(employee=emp):
        shifts = shifts | trainee.shifts.all()
    # Jobs
    for job in Job.objects.filter(employee=emp):
        shifts = shifts | job.shifts.all()
    # Office Hours
    for shift in OfficeHours.objects.filter(employee=emp):
        shifts = shifts | shift.shifts.all()
    shifts.order_by("time_out")[:25]
    return shifts
