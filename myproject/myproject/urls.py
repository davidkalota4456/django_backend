"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For smore information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.urls import path, include, re_path
from django.http import HttpResponse


def home_view(request):
    return HttpResponse("Welcome to my website!")


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view),
    path('myapp/', include('myapp.urls')),
    path('users/', include('users.urls')),
    path('user_admin/', include('user_admin.urls')),
    path('clients_msg/', include('clients_msg.urls')),
    path('zoommeetings/', include('zoommeetings.urls')),
    path('clients_projects/', include('clients_projects.urls')),
    
]
