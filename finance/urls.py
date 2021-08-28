from django.urls import path
from . import views

app_name = "finance"
urlpatterns = [
    path("", views.FinancialOverview.as_view(), name="overview"),
    path("estimate/<e_id>", views.viewEstimate.as_view(), name="estimate"),
    path("invoice/<e_id>", views.viewInvoice.as_view(), name="invoice"),
    path("timesheet/<pp_id>/<emp_id>", views.viewTimesheet.as_view(), name="timesheet"),
    path("summary/<pp_id>/", views.viewSummary.as_view(), name="summary"),
]
