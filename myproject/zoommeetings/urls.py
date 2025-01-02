from django.urls import path
from . import views

urlpatterns = [
    # URL for when the admin picks the available meeting date and time
    path('admin_pickes_when_he_avilbele/', views.admin_pickes_when_he_avilbele, name='admin_pickes_when_he_avilbele'),

    # URL for when the user picks a meeting
    path('user_pickes_a_meeting/', views.user_pickes_a_meeting, name='user_pickes_a_meeting'),

    # URL for when the admin schedules the meeting
    path('admin_schedule_meeting/', views.admin_scedual_the_meeting, name='admin_scedual_the_meeting'),

    path('get_all_zoom_meetings/', views.get_all_zoom_meetings, name='get_all_zoom_meetings'),

    path('get_zoom_meetings/', views.get_zoom_meetings, name='get_zoom_meetings'),

    # URL for when the admin deletes a zoom meeting
    path('delete-meeting/', views.delete_zoom_meeting, name='delete_zoom_meeting'),

    # URL for to get the clients req and prefarance for meetings 
    path('get_clients/', views.get_clients, name='get_clients'),

    # URL SUBMIT THE MEETING AND SEND CLIENTS THE INFORMATION ABOUT THE MEETING CREATION
    path('create_zoom_meeting/', views.create_zoom_meeting, name='create_zoom_meeting'),

    path('get_url_off_zoom_meeting/', views.get_url_off_zoom_meeting, name='get_url_off_zoom_meeting'),

    path('get_all_zoom_meetings_for_the_admin/', views.get_all_zoom_meetings_for_the_admin, name='get_all_zoom_meetings_for_the_admin'),


]
