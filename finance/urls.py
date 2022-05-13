from django.urls import path
from . import views

app_name = "finance"
urlpatterns = [
    path("", views.FinancialOverview.as_view(), name="overview"),
    path("estimate/<e_id>", views.viewEstimate.as_view(), name="estimate"),
    path("invoice/<e_id>", views.viewInvoice.as_view(), name="invoice"),
    path("timesheet/<pp_id>/<emp_id>", views.viewTimesheet.as_view(), name="timesheet"),
    path(
        "noprint/timesheet/<pp_id>/<emp_id>",
        views.ViewTimesheetNoPrint.as_view(),
        name="timesheetnoprint",
    ),
    path(
        "sign/timesheet/<timesheet_id>",
        views.SignTimesheet.as_view(),
        name="sign_timesheet",
    ),
    path(
        "rollover/<pp_id>/<emp_id>", views.RollOverAllShifts.as_view(), name="rollover"
    ),
    path("summary/<pp_id>/", views.viewSummary.as_view(), name="summary"),
    path("summary_csv/<pp_id>/", views.exportSummaryCSV.as_view(), name="summary_csv"),
    path(
        "summary/sa_billing/<month>/<year>/",
        views.saBillingSummary.as_view(),
        name="sa_billing_summary",
    ),
]
