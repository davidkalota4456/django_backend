import hashlib
from django.http import JsonResponse
from user_admin.models import CustomUserAdmin
from django.contrib.auth.models import User
from .models import User
import json
from django.contrib.sessions.models import Session
import secrets
from clients_msg.models import ClientMessage
from clients_projects.models import ClientProject
from django.utils.timezone import now
from django.contrib.sessions.backends.db import SessionStore


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


def generate_custom_csrf_token():
    return secrets.token_urlsafe(32)


def save_csrf_token(request):
    csrf_token = generate_custom_csrf_token()
    request.session['csrf_token'] = csrf_token
    request.session.save()
    return csrf_token


def login_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        csrf_token_key = request.headers.get('X-Custom-CSRFToken')

        # Validate CSRF token
        result = find_session_by_csrf_token_key(csrf_token_key)
        if not result:
            return JsonResponse({'error': 'CSRF token key not found or expired'}, status=403)

        # Session exists, use the existing session
        session_data = result['session_data']
            
        username = data.get('username')
        gmail = data.get('email')

        # Check for admin login first
        try:
            # Check if the user is an admin by matching username and email
            user_admin = CustomUserAdmin.objects.get(username=username, email=gmail)
            if user_admin:
                
                return JsonResponse({'message': 'Login successful! Welcome Admin!', 'role': 'admin'})
        except CustomUserAdmin.DoesNotExist:
            pass  # If not found as admin, continue to check regular user

        # Now, check if the user is a regular user
        try:
            user = User.objects.get(username=username, gmail=gmail)
            if not user:
                return JsonResponse({'message': 'username or password are wrong'}, status=400)

            # Regular user login successful, handle session
            session = Session.objects.get(session_key=csrf_token_key, expire_date__gte=now())
            session_data = session.get_decoded()

            # Ensure 'role' and 'username' are in session_data
            #if 'role' not in session_data or 'username' not in session_data:
            session_data['role'] = 'user'
            session_data['username'] = user.username

            session.session_data = SessionStore().encode(session_data)
            session.save()

            return JsonResponse({'message': 'Login successful! Welcome User!', 'role': 'user'})

        except User.DoesNotExist:
            return JsonResponse({'error': 'Invalid credentials for regular user'}, status=400)

    return JsonResponse({'error': 'Invalid method'}, status=405)




def csrf_token_view(request):
    print("CSRF token view called")
    csrf_token = save_csrf_token(request)
    session_key = request.session.session_key  
    print(f"Session Key------<<<>>>>>: {session_key}")
    return JsonResponse({'csrfToken': session_key})


def register_view(request):
    if request.method == 'POST':
        # Get the username, email, and password from the POST data
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Check if the user already exists
        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already exists'}, status=400)
        
        if User.objects.filter(email=email).exists():
            return JsonResponse({'error': 'Email already exists'}, status=400)

        # Create the new user
        try:
            # Use Django's create_user method to safely create a user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,  # Django will automatically hash the password
            )
            user.save()

            # Optionally, add the user to a specific group (like 'user' role) if needed
            # user.groups.add(group)  # Assuming you have predefined groups

            return JsonResponse({'message': 'User registered successfully!'}, status=201)

        except Exception as e:
            return JsonResponse({'error': f'Error registering user: {str(e)}'}, status=500)

    # Return error if the method is not POST
    return JsonResponse({'error': 'Invalid method, POST required'}, status=405)

def logout_view(request):
    # This will clear the session and log the user out
    request.session.flush()  # This removes all session data
    return JsonResponse({'message': 'Logged out successfully'})


def is_logged_in(request):
    user_role = request.session.get('role', None)
    if user_role:
        return JsonResponse({'message': f'Logged in as {user_role}'})
    else:
        return JsonResponse({'message': 'Not logged in'}, status=400)




def get_username_from_session(csrf_token_key):
    # Find the session by the csrf_token_key
    session_info = find_session_by_csrf_token_key(csrf_token_key)
    
    if session_info and 'username' in session_info['session_data']:
        # Return the username if it exists in the session data
        return session_info['session_data']['username']
    else:
        # If no username is found in the session data
        return None



def get_user_info(request):
    # Ensure the request method is GET
    if request.method == "GET":
        csrf_token_key = request.headers.get('X-Custom-CSRFToken')
        # Check if the user is logged in by looking for the username in the session
        username = get_username_from_session(csrf_token_key)
        if not username:
            return JsonResponse({"error": "User not logged in"}, status=403)

        # Retrieve the user's information from the database based on the username
        user_message = User.objects.filter(username=username).first()

        if not user_message:
            return JsonResponse({"error": "User not found in the database"}, status=404)

        # Get the user's gmail from the retrieved message
        gmail = user_message.gmail

        # Return the username and gmail as JSON response
        response_data = {
            "username": username,
            "gmail": gmail 
        }

        return JsonResponse(response_data, status=200)

    # Return an error if the request method is not GET
    return JsonResponse({"error": "Invalid request method"}, status=405)



def add_client_message(request):
    if request.method == "POST":
        try:
            # Parse the JSON body
            data = json.loads(request.body)

            # Extract fields from the request
            name = data.get("name")
            preferred_way_to_connect = data.get("preferred_way_to_connect", "EMAIL")
            gmail = data.get("gmail", None)
            whatsapp_number = data.get("whatsapp_number", None)
            msg_info = data.get("msg_info")
            is_client = data.get("is_client", False)

            # Validate required fields
            if not name or not msg_info:
                return JsonResponse({"error": "Name and msg_info are required fields."}, status=400)

            # Create and save the ClientMessage object
            client_message = ClientMessage.objects.create(
                name=name,
                preferred_way_to_connect=preferred_way_to_connect,
                gmail=gmail,
                whatsapp_number=whatsapp_number,
                msg_info=msg_info,
                is_client=is_client,
            )

            return JsonResponse(
                {"message": "Client message added successfully!", "id": client_message.id},
                status=201,
            )

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data."}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Invalid request method. Use POST."}, status=405)    
    


def get_client_projects(request):
    if request.method == "GET":
        try:
            # Retrieve the username (client_name) from the session
            client_name = request.session.get("username")

            if not client_name:
                return JsonResponse({"error": "No username found in the session."}, status=403)

            # Query projects for the client
            projects = ClientProject.objects.filter(client_name=client_name)

            # Prepare the project data for JSON response
            project_list = [
                {
                    "id": project.id,
                    "project_picture": project.project_picture.url if project.project_picture else None,
                    "completed": project.completed,
                    "project_info": project.project_info,
                    "time_to_complete": str(project.time_to_complete),
                }
                for project in projects
            ]

            return JsonResponse({"projects": project_list}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Invalid request method. Use GET."}, status=405)    
    



