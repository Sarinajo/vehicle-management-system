from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('',views.home, name='home'),
    path('success/<int:record_id>/', views.success, name='success'),
    path('login/',
         auth_views.LoginView.as_view(template_name='main/login.html'),
         name='login'),
    path('logout/',views.user_logout, name='logout'),
    path('register/', views.register, name='register'),
    path('my-records/', views.my_records, name='my_records'),
    path('reports/', views.reports, name='reports'),
    ]