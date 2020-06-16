from django.urls import path

from . import views

app_name = 'gig'

urlpatterns = [
    path('<int:gig_id>/', views.gigIndex, name='gigindex'),
    path('<int:system_id>/report-broken', views.reportBrokenEquipment, name='reportBroken'),
    path('', views.index, name='index'),
    path('signup/', views.signup, name='signup'),
    path('punch/', views.punch, name='punch'),
]
