from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_home, name='admin_home'),
    path('get_user_messages/', views.get_user_messages, name='get_user_messages'),
    path('respond_to_message/', views.respond_to_message, name='respond_to_message'), 
    path('register/', views.register_user, name='register_user'), 
    path('get_clients/', views.get_clients, name='get_clients'),
    path('get_clients_that_have_projects/', views.get_clients_that_have_projects, name='get_clients_that_have_projects'),
    path('add_project/', views.add_project, name='add_project'),
    path('update_project/', views.update_project, name='update_project'),
    path('admin_delete_user/', views.admin_delete_user, name='admin_delete_user'),
    path('admin_login_view/', views.admin_login_view, name='admin_login_view'),
    path('admin_update_itself/', views.admin_update_itself, name='admin_update_itself'),               
]
