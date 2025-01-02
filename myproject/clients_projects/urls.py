# urls.py
from django.urls import path
from .views import get_client_projects, create_client_project

urlpatterns = [
    # GET request to retrieve projects by client name
    path('projects-info/', get_client_projects, name='get_client_projects'),
    
    # POST request to create a project
    path('projects/', create_client_project, name='create_project'),
]
