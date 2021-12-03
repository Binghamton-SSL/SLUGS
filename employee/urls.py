from django.urls import path
from . import views

app_name = "employee"
urlpatterns = [
    path("onboard", views.userSignup.as_view(), name="signup"),
    path("onboard/success", views.userSignupComplete.as_view(), name="signup_complete"),
    path("view", views.userOverview.as_view(), name="overview"),
    path("password/change", views.changePassword.as_view(), name="change_password"),
    path("office_hours", views.officeHours.as_view(), name="office_hours"),
    path("form/<form_id>/upload", views.uploadForm.as_view(), name="upload_form"),
    path(
        "mass-assign-paperwork/<selected>",
        views.massAssignPaperwork.as_view(),
        name="mass_assign",
    ),
    path(
        "add-groups/<selected>",
        views.addGroups.as_view(),
        name="add_groups",
    ),
]
