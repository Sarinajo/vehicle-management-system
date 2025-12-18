from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('home/',views.home, name='home'),
    path('success/<int:record_id>/', views.success, name='success'),
    path('login/', views.user_login, name='login'),
    path('logout/',views.user_logout, name='logout'),
    path('register/', views.register, name='register'),
    path('my-records/', views.my_records, name='my_records'),
    path('reports/', views.reports, name='reports'),
    path('drivers/', views.manage_drivers, name='manage_drivers'),
    path('reports/raw-driver/', views.reports_raw_driver, name='reports_raw_driver'),
    path('reports/summary-driver/', views.reports_summary_driver, name='reports_summary_driver'),
    path('reports/raw-vehicle/', views.reports_raw_vehicle, name='reports_raw_vehicle'),
    path('reports/summary-vehicle/', views.reports_summary_vehicle, name='reports_summary_vehicle'),


    ]