from django.urls import path
from . import views  # Import views from the current app

urlpatterns = [
    # Define the route for bot communication
    path('', views.bot_communication, name='bot_communication'),  # This connects the URL '/bot/' to the view
]
