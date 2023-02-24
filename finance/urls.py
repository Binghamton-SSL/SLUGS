from django.urls import path
from . import views

app_name = "finance"
urlpatterns = [
    path("", views.FinancialOverview.as_view(), name="overview"),
    path("estimate/<e_id>", views.viewEstimate.as_view(), name="estimate"),
    path("invoice/<e_id>", views.viewInvoice.as_view(), name="invoice"),
    path("vendor/<v_id>", views.viewSubcontractedEquipment.as_view(), name="vendor"),
    path("timesheet/<timesheet_id>", views.viewTimesheet.as_view(), name="timesheet"),
    path(
        "noprint/timesheet/<timesheet_id>",
        views.ViewTimesheetXframe.as_view(),
        name="timesheetxframe",
    ),
    path(
        "sign/timesheet/<timesheet_id>",
        views.SignTimesheet.as_view(),
        name="sign_timesheet",
    ),
    path("summary/<pp_id>/", views.viewSummary.as_view(), name="summary"),
    path("summary_csv/<pp_id>/", views.exportSummaryCSV.as_view(), name="summary_csv"),
    path("summary_paychex_csv/<pp_id>/", views.exportSummaryPayChexCSV.as_view(), name="summary_paychex_csv"),
    path(
        "summary/sa_billing/<month>/<year>/",
        views.saBillingSummary.as_view(),
        name="sa_billing_summary",
    ),
]
