from django.urls import path

from . import views

app_name = 'employee'

urlpatterns = [
    path('', views.index, name='index'),
    path('change-password', views.change_password, name='changePassword'),
    path('onboard', views.signup, name='signup'),
]
