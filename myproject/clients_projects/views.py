from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from django.db.models import F
from .models import ClientProject
import json
from django.contrib.sessions.models import Session
from django.utils.timezone import now
import boto3
from django.conf import settings

from django.utils.timezone import now


def calculate_remaining_days(days, date_of_creation):
    days_elapsed = (now() - date_of_creation).days
    # Subtract elapsed days from time_to_complete
    remaining_days = max(0, days - days_elapsed)
    return remaining_days

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



def get_presigned_urls(username):
    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION
    )
    
    # The folder name corresponds to the user's username
    folder_name = f"{username}/"  # Assuming images are stored in folders named by username
    presigned_urls = []

    try:
        # List all objects in the user's folder
        response = s3_client.list_objects_v2(
            Bucket=settings.BUCKET_NAME,
            Prefix=folder_name
        )

        # Check if there are any files in the folder
        if 'Contents' in response:
            # Generate a presigned URL for each image
            for item in response['Contents']:
                image_key = item['Key']
                # Skip if the item is a folder (S3 uses keys as paths, but folders don't exist as separate entities)
                if image_key.endswith('/'):
                    continue

                # Get the Content-Type of the file
                content_type = s3_client.head_object(Bucket=settings.BUCKET_NAME, Key=image_key)['ContentType']

                # Generate the presigned URL for each file
                url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': settings.BUCKET_NAME, 'Key': image_key},
                    ExpiresIn=3600  # URL expiration time in seconds (1 hour)
                )

                # Append the URL and content type to the list
                presigned_urls.append({
                    'url': url,
                    'type': content_type
                })

        return presigned_urls

    except Exception as e:
        print(f"Error generating presigned URLs: {e}")
        return []


def get_client_projects(request):
    if request.method == 'GET':
        # Extract CSRF token from custom header
        csrf_token_key = request.headers.get('X-Custom-CSRFToken')
        if not csrf_token_key:
            return JsonResponse({"error": "CSRF token is missing"}, status=400)
        session_result = find_session_by_csrf_token_key(csrf_token_key)
        if not session_result:
            
            return JsonResponse({'error': 'CSRF token key not found or expired'}, status=403)

        session_data = session_result['session_data']
        username = session_data.get('username')
        user_type = session_data.get('role')
        if not username or (user_type != 'user' and user_type != 'admin'):
            return JsonResponse({'error': 'User not found in session'}, status=400)

        projects = ClientProject.objects.filter(client_name=username).values(
            'id', 'client_name', 'completed', 'project_info', 'time_to_complete', 'creation_date'
        )
        if not projects.exists():
            return JsonResponse({"error": "No projects found for this client"}, status=402)

        # Get presigned URLs for images associated with this user
        presigned_urls = get_presigned_urls(username)

        # Attach presigned URLs to each project (if any images exist) and calculate remaining days
        updated_projects = []
        for project in projects:
            project['project_picture_urls'] = presigned_urls  # You can customize how you attach URLs to each project
            project['remaining_days'] = calculate_remaining_days(
                project['time_to_complete'], project['creation_date']
            )
            updated_projects.append(project)

        response_data = {
            'username': username,  # Include username to greet the client
            'projects': updated_projects,  # Send the updated projects data with remaining days
        }

        # Return the projects as JSON
        return JsonResponse(response_data, safe=False)

    return JsonResponse({"error": "Method not allowed"}, status=405)



def create_client_project(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            # CSRF token validation
            csrf_token_key = request.headers.get('X-Custom-CSRFToken')
            result = find_session_by_csrf_token_key(csrf_token_key)
            if not result:
                return JsonResponse({'error': 'CSRF token key not found or expired'}, status=403)

            # Extract data from the request body
            client_name = data.get('client_name')
            project_picture = data.get('project_picture')
            completed = data.get('completed')
            project_info = data.get('project_info')
            time_to_complete = data.get('time_to_complete')

            # Validate required fields
            if not all([client_name, project_picture, completed, project_info, time_to_complete]):
                return JsonResponse({"error": "All fields are required"}, status=400)

            # Create the new project
            ClientProject.objects.create(
                client_name=client_name,
                project_picture=project_picture,
                completed=completed,
                project_info=project_info,
                time_to_complete=time_to_complete,
            )

            # Return a success message without project details
            return JsonResponse({"message": "Project added successfully"}, status=201)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Method not allowed"}, status=405)

# Create your views here.

def update_client_project(request):
    if request.method == 'PUT':
        try:
            # Fetch the project by ID
            try:
                data = json.loads(request.body)
                project_id = data['id']
                project = ClientProject.objects.get(id=project_id)
            except ClientProject.DoesNotExist:
                return JsonResponse({"error": "Project not found"}, status=404)

            # CSRF token validation
            csrf_token_key = request.headers.get('X-Custom-CSRFToken')
            result = find_session_by_csrf_token_key(csrf_token_key)
            if not result:
                return JsonResponse({'error': 'CSRF token key not found or expired'}, status=403)

            # Optional fields to update
            project_picture = data.get('project_picture')
            completed = data.get('completed')
            project_info = data.get('project_info')
            time_to_complete = data.get('time_to_complete')

            # Update only the fields that are provided
            if project_picture is not None:
                project.project_picture = project_picture
            if completed is not None:
                project.completed = completed
            if project_info is not None:
                project.project_info = project_info
            if time_to_complete is not None:
                project.time_to_complete = time_to_complete

            # Save the updated project
            project.save()

            # Return a success message after the update
            return JsonResponse({"message": "Project updated successfully"}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    # Method not allowed for anything other than PUT/PATCH
    return JsonResponse({"error": "Method not allowed"}, status=405)