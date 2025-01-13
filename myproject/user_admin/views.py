
from django.http import JsonResponse
from django.contrib.sessions.models import Session
from clients_msg.models import ClientMessage
from clients_projects.models import ClientProject
from users.models import User
from django.contrib.auth.hashers import check_password, make_password
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from users.models import User
from .models import CustomUserAdmin
import json
from datetime import datetime
from django.contrib.sessions.backends.db import SessionStore
from django.utils.timezone import now
from clients_msg.views import send_email_smtp
import hashlib

from django.conf import settings

s3 = boto3.client(
    's3',
    aws_access_key_id= settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION
)


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


def admin_login_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        csrf_token_key = request.headers.get('X-Custom-CSRFToken')

        # Retrieve session by CSRF token
        result = find_session_by_csrf_token_key(csrf_token_key)
        if result:
            # Session exists, use the existing session
            session_data = result['session_data']

        # Extract login data
        username = data.get('username')
        email = data.get('email')
        password = data.get('adminPassword')
        
        # Hash the entered password to compare with the stored password
        hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()

        try:
            # Retrieve user by username and email
            user_admin = CustomUserAdmin.objects.get(username=username, email=email)

            # Check if the hashed password matches the stored password
            if user_admin.password == hashed_password:
                
                session = Session.objects.get(session_key=csrf_token_key, expire_date__gte=now())
                session_data = session.get_decoded()

                # Ensure both 'role' and 'username' are in the session data
                if 'role' not in session_data or 'username' not in session_data or session_data['role'] == 'user':
                    session_data['role'] = 'admin'
                    session_data['username'] = user_admin.username

                    session.session_data = SessionStore().encode(session_data)
                    session.save()

                return JsonResponse({'message': 'Login successful! Welcome Admin!', 'success': True})

            else:
                return JsonResponse({'error': 'Invalid credentials'}, status=400)

        except CustomUserAdmin.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=400)

    return JsonResponse({"error": "Method not allowed"}, status=405)




def create_s3_folder_for_client(bucket_name, folder_name):
    try:
        # Create an empty file to represent the folder (S3 treats this as a folder)
        s3.put_object(Bucket=bucket_name, Key=f"{folder_name}/")

        print(f"Folder '{folder_name}' created in bucket '{bucket_name}'")

    except (NoCredentialsError, PartialCredentialsError) as e:
        print("Error: AWS credentials are missing or invalid.")
    except Exception as e:
        print(f"Error: {str(e)}")



def delete_s3_folder_for_user(bucket_name, username):
    try:
        folder_path = f"{username}/"
        

        # List all objects within the folder
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=folder_path)

        

        # If there are no objects in the folder, return a message
        if 'Contents' not in response:
            return {"message": f"No objects found for username '{username}'.", "deletedItems": 0}

        # Extract the keys (file paths) to delete
        keys_to_delete = [{"Key": item["Key"]} for item in response["Contents"] if item["Key"] != folder_path]

        # If there are files to delete, delete them
        deleted_count = 0
        if keys_to_delete:
            delete_response = s3.delete_objects(
                Bucket=bucket_name,
                Delete={"Objects": keys_to_delete}
            )
            deleted_count = len(delete_response.get("Deleted", []))
            
        delete_folder_response = s3.delete_objects(
            Bucket=bucket_name,
            Delete={"Objects": [{"Key": folder_path}]}
        )

        # Return success message
        return {
            "message": f"Successfully deleted '{username}' folder and its contents.",
            "deletedItems": deleted_count + 1  # +1 for the folder itself
        }

    except (NoCredentialsError, PartialCredentialsError) as e:
        return {"error": "AWS credentials are missing or invalid."}
    except Exception as e:
        return {"error": str(e)}



def check_folder_exists(bucket_name, client_name):
    """Check if a folder exists in the S3 bucket for the user and return the number of files inside."""
    try:
        # List objects in the folder (by client_name)
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=f"{client_name}/", Delimiter="/")
        
        # Check if 'Contents' is present, which indicates files exist in that folder
        if 'Contents' in response:
            file_count = len(response['Contents'])  # Count files
            return file_count
        return 0  # Return 0 if no files found
    except Exception as e:
        print(f"Error checking folder existence: {str(e)}")
        return 0  # Return 0 on error or failure



def upload_image_to_s3(file, bucket_name, client_name, object_name):
    """Upload an image file to S3."""
    try:
        # Set the correct content type based on the file extension
        content_type = file.content_type  # Automatically get the content type (e.g., image/png)
        
        # Upload the file to S3 with the content type specified
        s3.upload_fileobj(file, bucket_name, object_name, ExtraArgs={'ContentType': content_type})

        print(f"Image uploaded to {bucket_name}/{object_name}")
    except NoCredentialsError:
        print("AWS credentials not available.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


def update_project(request):
    if request.method == "POST":
        try:
            csrf_token_key = request.POST.get("csrf_token")
            if not find_session_scrf_admin(csrf_token_key):
                return JsonResponse({'error': 'CSRF token key not found or expired'}, status=403)
             #Parse request data
            client_name = request.POST.get('clientName')
            new_end = request.POST.get('endDate')
            new_info = request.POST.get('projectInfo')
            image_file = request.FILES.get('projectPicture')
            bucket_name = settings.BUCKET_NAME

            # Validate input
            if not client_name:
                return JsonResponse({'error': 'Client name is required'}, status=400)
            if not image_file and not new_end and not new_info:
                return JsonResponse({'error': 'No updates provided'}, status=400)

            # Find project
            found_project = ClientProject.objects.filter(client_name=client_name).first()
            if not found_project:
                return JsonResponse({'error': 'Project not found for the given client'}, status=404)

            # Update fields
            if new_info != '':
                found_project.project_info = new_info

            if new_end != '':
                try:
                    new_end_date = datetime.strptime(new_end, '%Y-%m-%d').date()
                    new_days = (new_end_date - found_project.start_date).days
                    found_project.time_to_complete = new_days
                except ValueError:
                    return JsonResponse({'error': 'Invalid date format for endDate'}, status=400)

            if image_file:
                file_count = check_folder_exists(bucket_name, client_name)
                object_name = f"{client_name}/imageorvideo{file_count + 1}"
                upload_image_to_s3(image_file, bucket_name, client_name, object_name)

                

            # Save changes
            found_project.save()
            return JsonResponse({'message': 'Project updated successfully'}, status=200)

        except Exception as e:
            return JsonResponse({'error': f"An unexpected error occurred: {str(e)}"}, status=500)

    return JsonResponse({'message': 'Invalid request method.'}, status=405)





# Admin dashboard home (just a placeholder response)
def admin_home(request):
    return JsonResponse({'message': 'Welcome to the Admin Dashboard'}, status=200)


def get_clients(request):
    if request.method == "GET":
        try:
            csrf_token_key = request.headers.get('X-Custom-CSRFToken')
            result = find_session_scrf_admin(csrf_token_key)
            if not result:
                return JsonResponse({'error': 'CSRF token key not found or expired'}, status=403)
            users = User.objects.all().values('username')  # Only select the username field
            usernames = [user['username'] for user in users]  # Create a list of usernames
        
            return JsonResponse({'clients': usernames}, status=200)
        except Exception as e:
            return JsonResponse({'message': 'Failed to fetch clients.', 'error': str(e)}, status=500)


def get_clients_that_have_projects(request):
    if request.method == "GET":
        try:
            csrf_token_key = request.headers.get('X-Custom-CSRFToken')
            result = find_session_scrf_admin(csrf_token_key)
            if not result:
                return JsonResponse({'error': 'CSRF token key not found or expired'}, status=403)
            
            users = ClientProject.objects.all().values('client_name')  # Only select the username field
            usernames = [user['client_name'] for user in users]  # Create a list of usernames
            
            return JsonResponse({'clients': usernames}, status=200)
        except Exception as e:
            return JsonResponse({'message': 'Failed to fetch clients.', 'error': str(e)}, status=500)


def register_user(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            csrf_token_key = request.headers.get('X-Custom-CSRFToken')
            result = find_session_scrf_admin(csrf_token_key)
            if not result:
                return JsonResponse({'error': 'CSRF token key not found or expired'}, status=403)
            
            username = data.get("username")
            gmail = data.get("email")

            # Validate that both fields are provided
            if not username or not gmail:
                return JsonResponse({"status": "error", "message": "Username and email are required."}, status=400)

            # Check if the user already exists
            if User.objects.filter(username=username).exists():
                return JsonResponse({"status": "error", "message": "Username already exists."}, status=400)
            if User.objects.filter(gmail=gmail).exists():
                return JsonResponse({"status": "error", "message": "Email already registered."}, status=400)

            # Create a new user (password is optional for this example)
            user = User(username=username, gmail=gmail)
            user.save()

            return JsonResponse({"status": "success", "message": "User registered successfully!"}, status=201)
        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON data."}, status=400)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    else:
        return JsonResponse({"status": "error", "message": "Invalid HTTP method."}, status=405)






def respond_to_message(request):
    if request.method == "POST":
        try:
            csrf_token_key = request.headers.get('X-Custom-CSRFToken')
            result = find_session_scrf_admin(csrf_token_key)
            if not result:
            
                return JsonResponse({'error': 'CSRF token key not found or expired'}, status=403)
            data = json.loads(request.body)
            user_name = data.get("userName")
            gmail = data.get("gmail")
            msg = data.get("response")
            
            # Check if all required fields are provided
            if not user_name or not gmail or not msg:
                return JsonResponse({"status": "error", "message": "Missing required fields"})

            # Prepare the email subject and body
            sub = f"Welcome {user_name}!"
            
            # Call the send_email_smtp function to send the email
            send_email_smtp(gmail, sub, user_name, msg)
            message = ClientMessage.objects.filter(name=user_name, gmail=gmail, admin_response__isnull=True).first()
            if message:
                
                message.delete()
            else:
                return JsonResponse({"status": "error", "message": "No matching message found or already responded"})    

            return JsonResponse({"status": "success", "message": "Message responded and email sent successfully"})

        except Exception as e:
            return JsonResponse({"status": "error", "message": f"An error occurred: {str(e)}"})
    
    return JsonResponse({"status": "error", "message": "Invalid request method"})


# View for managing users


# Analytics view
def get_user_messages(request):
    if request.method == 'GET':
        csrf_token_key = request.headers.get('X-Custom-CSRFToken')
        result = find_session_scrf_admin(csrf_token_key)
        if not result:

            return JsonResponse({'error': 'CSRF token key not found or expired'}, status=403)
        user_messages = {}
        messages = ClientMessage.objects.filter(admin_response__isnull=True)  # Retrieve all messages from the database
        
        for message in messages:
            user_messages[message.name] = {
                'message': message.msg_info,
                'responded': message.admin_response,
                'gmail': message.gmail,
                'number': message.whatsapp_number,
                'number': message.preferred_way_to_connect,
            }
        
        return JsonResponse({'user_messages': user_messages})
    
    # If the method is not GET, return a Method Not Allowed response
    return JsonResponse({'error': 'Method not allowed. Only GET requests are supported.'}, status=405)


def add_project(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            # CSRF token validation
            csrf_token_key = request.headers.get('X-Custom-CSRFToken')
            result = find_session_scrf_admin(csrf_token_key)
            if not result:
                return JsonResponse({'error': 'CSRF token key not found or expired'}, status=403)

            client_name = data.get('clientName')
            project_info = data.get('projectInfo')
            completed = False
            start_date = data.get('startDate')
            end_date = data.get('endDate')
            
            # Validate date fields
            if not (start_date and end_date):
                return JsonResponse({'message': 'Start and end dates are required.'}, status=400)

            # Parse start_date and end_date
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            except ValueError:
                return JsonResponse({'message': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

            # Calculate the total number of days
            days_to_complete = (end_date_obj - start_date_obj).days
            if days_to_complete < 0:
                return JsonResponse({'message': 'End date must be after start date.'}, status=400)

            # Create a new ClientProject instance
            project = ClientProject.objects.create(
                client_name=client_name,
                project_picture=None,
                completed=completed,
                project_info=project_info,
                time_to_complete= int(days_to_complete),
                start_date=start_date_obj
            )
            folder_name = client_name  # Only use the client name for the folder
            bucket_name = settings.BUCKET_NAME

            create_s3_folder_for_client(bucket_name, folder_name)

            return JsonResponse({'message': 'Project added successfully!', 'project_id': project.id}, status=201)

        except Exception as e:
            return JsonResponse({'message': 'Failed to add project.', 'error': str(e)}, status=500)

    return JsonResponse({'message': 'Invalid request method.'}, status=405)


def admin_delete_user(request):
    if request.method == "POST":
        try:
            # Extract CSRF token key from headers
            csrf_token_key = request.headers.get('X-Custom-CSRFToken')
            result = find_session_scrf_admin(csrf_token_key)
            if not result:
                return JsonResponse({'error': 'CSRF token key not found or expired'}, status=403)

            # Parse the request body
            data = json.loads(request.body)
            client_name = data.get('clientName')

            # Check if the user exists
            user = User.objects.filter(username=client_name).first()
            if not user:
                return JsonResponse({'error': f'User with username "{client_name}" not found.'}, status=404)

            # Find and delete the user's projects
            projects = ClientProject.objects.filter(client_name=client_name)
            deleted_projects_count = projects.delete()[0]  

            # Delete the user's S3 folder and contents
            bucket_name = settings.BUCKET_NAME
            
            s3_delete_result = delete_s3_folder_for_user(bucket_name, client_name)
            

            
            user.delete()

            # Return success response
            return JsonResponse({
                'message': 'User and associated projects deleted successfully.',
                'deletedProjectsCount': deleted_projects_count,
                'deletedUser': client_name,
                's3DeleteResult': s3_delete_result  # Include S3 deletion details
            }, status=200)

        except Exception as e:
            return JsonResponse({
                'message': 'Failed to delete user and projects.',
                'error': str(e)
            }, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method. Only POST is allowed.'}, status=405)




def admin_update_itself(request):
    if request.method == "POST":
        try:
            # Parse request data
            data = json.loads(request.body)
            # CSRF token validation
            csrf_token_key = request.headers.get('X-Custom-CSRFToken')

            result = find_session_scrf_admin(csrf_token_key)
            if not result:
                return JsonResponse({'error': 'CSRF token key not found or expired'}, status=403)
            
            # Extract fields from the request data
            client_name = data.get('userName')
            password = data.get('password')
            new_email = data.get('email')

            new_password = hashlib.sha256(password.encode('utf-8')).hexdigest()

            # Check if the admin user exists
            admin_user = CustomUserAdmin.objects.filter(username=client_name, email=new_email).first()
            if not admin_user:
                return JsonResponse({'error': 'Admin user not found.'}, status=404)

            admin_user.password = new_password
           
            admin_user.save()

            return JsonResponse({'message': 'Admin user updated successfully.'}, status=200)
        
        except Exception as e:
            return JsonResponse({
                'message': 'Failed to update admin user.',
                'error': str(e)
            }, status=500)

    return JsonResponse({'message': 'Invalid request method.'}, status=405)