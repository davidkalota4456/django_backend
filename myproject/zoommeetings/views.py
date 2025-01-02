#from django.shortcuts import render
from datetime import datetime
import pytz
from django.http import JsonResponse
from .models import ZoomMeeting
from clients_msg.models import ClientMessage
import json
from django.contrib.sessions.models import Session
from django.utils.timezone import now
from django.contrib.sessions.backends.db import SessionStore
from users.models import User
from clients_msg.views import send_email_smtp
from django.contrib.sessions.models import Session
from django.db.models import Q

def find_session_scrf_admin(csrf_token_key):
    try:
        session = Session.objects.get(session_key=csrf_token_key, expire_date__gte=now())
        session_data = session.get_decoded()
        if session_data.get('role') == 'admin':
           return True
        return False
    except Session.DoesNotExist:
        return None

def find_session_by_csrf_token_key(csrf_token_key):
    # Query for the active session where the session_key matches csrf_token_key
    try:
        session = Session.objects.get(session_key=csrf_token_key, expire_date__gte=now())
        session_data = session.get_decoded()
        
        return {
            'session_id': session.session_key,  # This is the session's unique ID
            'session_data': session_data,       # Decoded session data
        }
    except Session.DoesNotExist:
        return None




def convert_to_client_time(admin_time, client_timezone):
    # Define the timezone for Israel (Admin)
    israel_tz = pytz.timezone('Asia/Jerusalem')
    
    # Convert admin time to datetime object in Israel timezone
    admin_time = israel_tz.localize(admin_time)

    # Define the client's timezone (e.g., New York)
    client_tz = pytz.timezone(client_timezone)
    
    # Convert the time to the client's timezone
    client_time = admin_time.astimezone(client_tz)

    return client_time

def format_time_for_display(client_time):
    # Format time to be easily readable
    return client_time.strftime("%Y-%m-%d %H:%M:%S %Z%z")



def convert_admin_israel_to_utc(admin_meeting_time):
    # Define the Israel timezone
    israel_timezone = pytz.timezone('Asia/Jerusalem')
    
    # Localize the admin meeting time (assuming it's in Israel's timezone)
    localized_admin_time = israel_timezone.localize(admin_meeting_time)
    
    # Convert the localized time to UTC
    utc_time = localized_admin_time.astimezone(pytz.utc)
    
    return utc_time



def admin_pickes_when_he_avilbele(request):
    if request.method == 'POST':
        try:
            # Parse the incoming data
            data = json.loads(request.body)

            csrf_token_key = request.headers.get('X-Custom-CSRFToken')
            if not find_session_scrf_admin(csrf_token_key):
                return JsonResponse({'error': 'CSRF token key not found or expired'}, status=403)

            date = data.get('date')  # Get the date (YYYY-MM-DD)
            hour = data.get('hour')  # Get the hour (HH:MM)

            # Check if both date and hour are provided
            if not date or not hour:
                return JsonResponse({'message': 'Date and hour are required.'}, status=400)

            # Combine the date and hour into a full datetime string (e.g., 'YYYY-MM-DD HH:MM:00')
            date_time_str = f"{date} {hour}:00"
            admin_meeting_time = datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S')
            

            # Convert the admin meeting time from Israel timezone to UTC
            utc_time = convert_admin_israel_to_utc(admin_meeting_time)
            
            # Save the meeting with both the Israel meeting time and UTC time
            zoom_meeting = ZoomMeeting.objects.create(
                admin_meeting_time=admin_meeting_time,  # Store the admin's time (Israel's timezone)
                utc_time=utc_time,  # Store the UTC time
            )

            return JsonResponse({'message': 'Zoom meeting scheduled successfully!', 'meeting_id': zoom_meeting.id}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'message': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'message': f'An error occurred: {str(e)}'}, status=500)



def user_pickes_a_meeting(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        csrf_token_key = request.headers.get('X-Custom-CSRFToken')
        result = find_session_by_csrf_token_key(csrf_token_key)
        if not result:
            return JsonResponse({'error': 'CSRF token key not found or expired'}, status=403)

        session = Session.objects.get(session_key=csrf_token_key, expire_date__gte=now())
        session_data = session.get_decoded()

        username = session_data['username']

        if username:
            print('Username:', username)
            user = User.objects.get(username=username)
            gmail = user.gmail

        datetime_str = data.get('date') 
        user_timezone = data.get('timezone') 
        print('im the addres', user_timezone)

        
        
        # Validate if date, hour, and timezone are provided
        if not datetime_str or not user_timezone:
            return JsonResponse({'message': 'Date and timezone are required.'}, status=400)

        # Combine date and hour into a datetime object (assuming date is in 'YYYY-MM-DD' and hour in 'HH:MM')
        try:
            utc_time = datetime.fromisoformat(datetime_str)

            print('Received UTC time:', utc_time)

            # Try to find the meeting by UTC date and time
            zoom_meeting = ZoomMeeting.objects.filter(utc_time=utc_time).first()

            if not zoom_meeting:
                print('--dident mack the backend--')

            if zoom_meeting:
                print('--I DID IT FULLY--')
                # Update the existing meeting with new client name and Gmail
                zoom_meeting.client_name = username
                zoom_meeting.client_gmail = gmail  # Add user's Gmail to the meeting
                zoom_meeting.save()

                return JsonResponse({
                    'status': 'success',
                    'message': 'SEND REQUEST TO ADMIN!',
                }, status=200)

            else:
                return JsonResponse({'message': 'Zoom meeting not found for the specified date and time.'}, status=404)

        except Exception as e:
            return JsonResponse({'message': f'An error occurred: {str(e)}'}, status=500)


def admin_scedual_the_meeting(request):
    if request.method == 'POST':
        try:

            data = json.loads(request.body)
            csrf_token_key = request.headers.get('X-Custom-CSRFToken')
            if not find_session_scrf_admin(csrf_token_key):
                return JsonResponse({'error': 'CSRF token key not found or expired'}, status=403)
            
            username = data.get('username')  # Get the username (nullable)
            duration = data.get('duration')  # Duration is nullable
            meeting_id = data.get('meeting_id')  # The ID of the meeting
            id = data.get('id')  # The primary key (model ID) for finding the Zoom meeting
            join_url = data.get('join_url')  # Join URL, nullable
            gmail = data.get('gmail')  # Gmail, nullable
            
            # Validate the required fields
            if not id:
                return JsonResponse({'message': 'Meeting ID (primary key) is required.'}, status=400)
            if not meeting_id:
                return JsonResponse({'message': 'Meeting ID is required.'}, status=400)

            # Try to find the meeting by its primary key (model ID)
            try:
                zoom_meeting = ZoomMeeting.objects.get(id=id)  # Using the normal model ID (primary key)

                # Update the meeting details with the provided data
                if username:
                    zoom_meeting.client_name = username  # Set the client name if provided
                if duration is not None:
                    zoom_meeting.duration = duration  # Set the duration if provided
                zoom_meeting.meeting_id = meeting_id  # Update the meeting ID
                if join_url:
                    zoom_meeting.join_url = join_url  # Update the join URL if provided
                if gmail:
                    zoom_meeting.gmail = gmail  # Update Gmail if provided

                # Save the updated Zoom meeting
                zoom_meeting.save()

                # Return the success response
                return JsonResponse({
                    'message': 'Zoom meeting scheduled successfully!',
                    'meeting_id': zoom_meeting.id,
                    'client_name': zoom_meeting.client_name,
                    'date': zoom_meeting.date,
                    'time': zoom_meeting.time,
                    'join_url': zoom_meeting.join_url,
                    'gmail': zoom_meeting.gmail,
                }, status=200)

            except ZoomMeeting.DoesNotExist:
                return JsonResponse({'message': 'Zoom meeting not found.'}, status=404)

        except json.JSONDecodeError:
            return JsonResponse({'message': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'message': f'An error occurred: {str(e)}'}, status=500)



def get_all_zoom_meetings_for_the_admin(request):
    if request.method == 'GET':
        try:
            csrf_token_key = request.headers.get('X-Custom-CSRFToken')
            
            
            if not find_session_scrf_admin(csrf_token_key):
                return JsonResponse({'error': 'CSRF token key not found or expired'}, status=403)
            
            # Retrieve all Zoom meetings with a valid join_url
            zoom_meetings = ZoomMeeting.objects.filter(join_url__isnull=False)
            
            # Check if no meetings were found
            if not zoom_meetings.exists():
                return JsonResponse({'message': 'No Zoom meetings found.'}, status=200)

            # If meetings are found, return them in the response
            meetings_data = [{
                'meeting_id': meeting.meeting_id,
                'client_name': meeting.client_name,
                'join_url': meeting.join_url,
                'time': meeting.utc_time,
            } for meeting in zoom_meetings]

            return JsonResponse({'meetings': meetings_data}, status=200)
        
        except Exception as e:
            return JsonResponse({'error': f'An unexpected error occurred: {str(e)}'}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=405)

def get_url_off_zoom_meeting(request):
    if request.method != 'GET':
        return JsonResponse({"error": "Invalid request method."}, status=405)
    try:
        csrf_token_key = request.headers.get('X-Custom-CSRFToken')
        # Validate CSRF token
        session_data = find_session_by_csrf_token_key(csrf_token_key)
        if not session_data:
            return JsonResponse({'error': 'CSRF token key not found or expired'}, status=403)
        
        username = session_data['session_data']['username']  # Correctly access username
        print('im username', username)
        
        try:
            # Filter ZoomMeeting by client_name and any other conditions, e.g., is_active
            zoom_meeting = ZoomMeeting.objects.filter(client_name=username, join_url__isnull=False).first()  # Adjust conditions as needed
            
            if not zoom_meeting:
                print('im stuck here')
                return JsonResponse({'message': 'No Zoom meetings found for the user.'}, status=200)  # No Zoom meeting found
            
            return JsonResponse({'join_url': zoom_meeting.join_url}, status=200)
        
        except ZoomMeeting.DoesNotExist:
            return JsonResponse({'error': 'Zoom meeting not found.'}, status=404)
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'An unexpected error occurred: {str(e)}'}, status=500)




def delete_zoom_meeting(request):
    if request.method == 'POST':
        try:
            # Parse the incoming JSON data
            data = json.loads(request.body)
            csrf_token_key = request.headers.get('X-Custom-CSRFToken')
            if not find_session_scrf_admin(csrf_token_key):
                return JsonResponse({'error': 'CSRF token key not found or expired'}, status=403)
            meeting_id = data.get('meeting_id')  # Get meeting ID from the request
            
            if not meeting_id:
                return JsonResponse({'message': 'Meeting ID is required.'}, status=400)
            
            try:
                # Retrieve the ZoomMeeting object using the meeting_id
                zoom_meeting = ZoomMeeting.objects.get(id=meeting_id)
                zoom_meeting.delete_meeting()  # Call the method to delete the meeting
                
                return JsonResponse({'message': 'Meeting deleted successfully!'}, status=200)
            except ZoomMeeting.DoesNotExist:
                return JsonResponse({'message': 'Zoom meeting not found.'}, status=404)

        except json.JSONDecodeError:
            return JsonResponse({'message': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'message': f'An error occurred: {str(e)}'}, status=500)




def convert_admin_time_to_all_timezones(admin_time):
    # Define the timezone for Israel (Admin's timezone)
    israel_tz = pytz.timezone('Asia/Jerusalem')
    
    # Localize the admin time (Israel time)
    admin_time = israel_tz.localize(admin_time)

    # List of timezones (including European time zones)
    all_timezones = [
        'Africa/Abidjan', 'America/New_York', 'Asia/Tokyo', 'Europe/London', 'Europe/Paris', 'America/Los_Angeles',
        'Asia/Kolkata', 'Australia/Sydney', 'Europe/Zurich', 'America/Sao_Paulo',
        'Europe/Berlin', 'Europe/Amsterdam', 'Europe/Madrid', 'Europe/Rome', 'Europe/Prague', 'Europe/Stockholm',
        'Europe/Brussels', 'Europe/Vienna', 'Europe/Helsinki', 'Europe/Oslo', 'Europe/Dublin'
    ]

    # Create a dictionary to store the converted times
    timezone_times = {}

    # Convert the admin time (Israel time) to all the timezones
    for tz_name in all_timezones:
        client_tz = pytz.timezone(tz_name)
        client_time = admin_time.astimezone(client_tz)
        timezone_times[tz_name] = client_time.strftime("%Y-%m-%d %H:%M:%S %Z%z")

    return timezone_times



def get_zoom_meetings(request):
    if request.method == 'GET':
        try:
            csrf_token_key = request.headers.get('X-Custom-CSRFToken')
            if not find_session_by_csrf_token_key(csrf_token_key):
                return JsonResponse({'error': 'CSRF token key not found or expired'}, status=403)
                
            # Filter ZoomMeeting objects where client_name and client_gmail are None
            meetings = ZoomMeeting.objects.filter(
                Q(client_name__isnull=True) | Q(client_name=''),
                Q(client_gmail__isnull=True) | Q(client_gmail='')
            ).values('utc_time')

            if meetings.exists():
                return JsonResponse({'meetings': list(meetings)}, status=200)
            else:
                return JsonResponse({'message': 'No Zoom meetings found.'}, status=404)
        except Exception as e:
            # In case of any unexpected error
            return JsonResponse({'message': f'Error fetching Zoom meetings: {str(e)}'}, status=500)


def get_all_zoom_meetings(request):
    if request.method == 'GET':
        try:
            csrf_token_key = request.headers.get('X-Custom-CSRFToken')
            if not find_session_scrf_admin(csrf_token_key):
                return JsonResponse({'error': 'CSRF token key not found or expired'}, status=403)
            meetings = ZoomMeeting.objects.all()

            # Serialize the data into a list of dictionaries
            data = [
                {
                    "clientName": meeting.client_name or 'Unknown Client',  # Use default if None
                    "clientGmail": meeting.client_gmail or 'No email provided',  # Use default if None
                    "meetingDate": meeting.admin_meeting_time.strftime('%Y-%m-%d %H:%M:%S'),
                    "meetingId": meeting.id,
                }
                for meeting in meetings
]

            

            return JsonResponse({'meetings': data}, safe=False)


        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)

def get_clients(request):
    if request.method == 'GET':
        csrf_token_key = request.headers.get('X-Custom-CSRFToken')
        if not find_session_scrf_admin(csrf_token_key):
            return JsonResponse({'error': 'CSRF token key not found or expired'}, status=403)
        
        meetings = ZoomMeeting.objects.filter(
            client_name__isnull=False,  # Condition 1: client_name is not null
            client_gmail__isnull=False,
       
        )

        # Serialize the filtered data into a list of dictionaries
        data = [
            {
                "clientName": meeting.client_name,
                "clientGmail": meeting.client_gmail, 
                "meetingDate": meeting.admin_meeting_time.strftime('%Y-%m-%d %H:%M:%S'),# its date and hour 2024-12-11 21:00:00.000000
                
            }
            for meeting in meetings
        ]

        return JsonResponse(data, safe=False)  # Return data as JSON
    return JsonResponse({"error": "Invalid request method."}, status=405)



def create_zoom_meeting(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            csrf_token_key = request.headers.get('X-Custom-CSRFToken')
            if not find_session_scrf_admin(csrf_token_key):
                return JsonResponse({'error': 'CSRF token key not found or expired'}, status=403)
            
            client_name = data.get('clientName')
            client_gmail = data.get('clientGmail')
            meeting_date = data.get('meetingDate')
            zoom_url = data.get('zoomUrl')
            meeting_id = data.get('meetingId')

            # Validate the required fields
            if not client_name or not zoom_url or not meeting_id:
                print(f'One of these values is not found: client_name={client_name},zoom_url={zoom_url}, meeting_id={meeting_id},client_gmail={client_gmail},meetingDate={meeting_date}')
                return JsonResponse({"error": "client_name, zoom_url, and meeting_id are required."}, status=400)

            # Find the Zoom meeting based on client_name (assuming client_name is unique)
            zoom_meeting_find = ZoomMeeting.objects.filter(
                client_name=client_name,
                admin_meeting_time=meeting_date
                ).first()  

            # If the meeting doesn't exist, return an error message
            if not zoom_meeting_find:
                return JsonResponse({"error": "No Zoom meeting found for this client."}, status=400)

            # Update the meeting details
            zoom_meeting_find.duration = 40  # Assuming you want a static duration (adjust if needed)
            zoom_meeting_find.topic = "Apps Development"  # Adjust the topic as per requirement
            zoom_meeting_find.meeting_id = meeting_id
            zoom_meeting_find.join_url = zoom_url
            zoom_meeting_find.save()

            client_email = zoom_meeting_find.client_gmail
            utc_meeting = zoom_meeting_find.utc_time
            # TODO CONVERT TO USER TIME
            send_email_smtp(
                receiver_email=client_email,
                subject=f"Zoom Meeting Update for {client_name}",
                username=client_name,
                body=f"Your Zoom meeting has been updated.\nDetails:\nMeeting ID: {meeting_id}\nZoom URL: {zoom_url}"
            )

            # TODO IN HERE THERE NEED BE A GMAIL SENDER ABOUT THIS ZOOM MEETING TO CLIENT

            return JsonResponse({"message": "Zoom meeting updated successfully!"}, status=200)
        
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format."}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    else:
        return JsonResponse({"error": "Only POST method is allowed."}, status=405)