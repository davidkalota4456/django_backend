from django.urls import path
from . import views

urlpatterns = [
    path('get_response/', views.get_admin_response, name='get_admin_response'),
    path('post_user_message/', views.post_user_message, name='post_user_message'),
    path('admin_responde_to_client_gmail/', views.admin_responde_to_client_gmail, name='admin_responde_to_client_gmail'),
    path('get_pasing_bay_msg/', views.get_pasing_bay_msg, name='get_pasing_bay_msg'),
]
