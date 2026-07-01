from django.urls import path
from . import views

urlpatterns = [
    path('', views.register, name='register'),
    path('success/<int:pk>/', views.registration_success, name='registration_success'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('report/', views.report, name='report'),
    path('report/export/', views.export_report_excel, name='export_report_excel'),
    path('check-duplicate/', views.check_duplicate, name='check_duplicate'),
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/edit/<int:pk>/', views.user_edit, name='user_edit'),
    path('users/delete/<int:pk>/', views.user_delete, name='user_delete'),
]
