from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login_view'),
    path('data/', views.get_user_info, name='get_user_info'),
    path('register/', views.register_view, name='register'),
    path('csrf/', views.csrf_token_view, name='csrf-token'),
    path('logout/', views.logout_view, name='logout_view'),
    path('is_logged_in/', views.is_logged_in, name='is_logged_in'),
]
