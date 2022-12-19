"""SLUGS URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
import debug_toolbar
from SLUGS import views
from django.contrib.auth import views as auth_views
from employee.views import FormDownload, FilledFormDownload
from finance.views import EstimateDownload
from django.views.generic.base import RedirectView


urlpatterns = [
    path("unicorn/", include("django_unicorn.urls")),
    path("tinymce/", include("tinymce.urls")),
    path("__debug__/", include(debug_toolbar.urls)),
    path("hijack/", include("hijack.urls")),
    path('admin/doc/', include('django.contrib.admindocs.urls')),
    path('openid/', include('oidc_provider.urls', namespace='oidc_provider')),
    path('.well-known/openid-configuration', RedirectView.as_view(url='/openid/.well-known/openid-configuration', permanent=False), name='openid-configuration'),
    path("admin/", admin.site.urls),
    path(
        "media/forms/<path:relative_path>", FormDownload.as_view(), name="download_form"
    ),
    path(
        "media/uploads/<u_pk>/<path:relative_path>",
        FilledFormDownload.as_view(),
        name="download_form",
    ),
    path(
        "media/estimates/<path:relative_path>",
        EstimateDownload.as_view(),
        name="download_estimate",
    ),
    path(
        "auth/password_reset/",
        auth_views.PasswordResetView.as_view(
            html_email_template_name="registration/password_reset_html_email.html"
        ),
    ),
    path("auth/", include("django.contrib.auth.urls"), name="auth"),
    path("utils/", include("utils.urls")),
    path("", views.index.as_view(), name="index"),
    path("kiosk/", views.kiosk.as_view(), name="kiosk"),
    path("employee/", include("employee.urls")),
    path("gig/", include("gig.urls")),
    path("equipment/", include("equipment.urls")),
    path("training/", include("training.urls")),
    path("finance/", include("finance.urls")),
]
