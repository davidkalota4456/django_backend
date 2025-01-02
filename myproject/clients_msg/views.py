from django.http import JsonResponse
from .models import ClientMessage
import smtplib
import json
from users.models import User
from django.contrib.sessions.models import Session
from django.utils.timezone import now
from django.conf import settings

def get_user_email_by_username(username):
    try:
        # Query the User model to get the user object
        user = User.objects.get(username=username)
        # Extract the email from the user object
        return user.gmail
    except User.DoesNotExist:
        return f"User with username '{username}' does not exist."

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

def send_email_smtp(receiver_email, subject, username, body):
    sender_email = settings.ENV_SENDER_EMAIL
    password = settings.ENV_PASSWORD

    # Use string formatting to dynamically insert the username in the subject
    subject = f"Welcome {username}!"  # Correct the subject to include the dynamic username

    # Prepare the email message with subject and body
    email_message = f"Subject: {subject}\n\n{body}"  # Combine subject and body into the message

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Start a secure connection
            server.login(sender_email, password)  # Login with your email and password
            server.sendmail(sender_email, receiver_email, email_message)  # Send the email
            print(f"Email sent to {receiver_email}!")
            return True
    except Exception as e:
        print(f"Failed to send email: {e}")


def admin_responde_to_client_gmail(request):
    if request.method == "POST":
        data = json.loads(request.body)  # Parse the incoming JSON data
        
        # Extract values using square brackets
        client_gmail = data['client_gmail']  # Extract the 'client_gmail' field
        username = data['username']  # Extract the 'username' field
        subject = data['subject']  # Extract the 'subject' field
        body = data.get('body', "Thank you for reaching out!")  # Get body content from the request, default to a placeholder if missing
        
        # Send the email
        email_sent = send_email_smtp(client_gmail, subject, username, body)
        
        # Check if the email was sent successfully
        if email_sent:
            return JsonResponse({'message': 'Email sent successfully!'}, status=200)  # Success response
        else:
            return JsonResponse({'error': 'Failed to send email'}, status=500)  # Error response if sending fails


def get_pasing_bay_msg(request):
    if request.method == "POST":
        try:
            # Parse the incoming JSON data
            data = json.loads(request.body)
            
            # Extract values
            gmail = 'davidkalota64@gmail.com'
            client_gmail = data.get('email')  # Safely extract email
            username = data.get('username')  # Safely extract username
            data_field = data.get('message')  # Safely extract message
            
            # Ensure all required fields are present
            if not client_gmail or not username or not data_field:
                return JsonResponse({'error': 'Missing required fields'}, status=400)
            
            # Compose the email subject and body
            subject = f"Message from {username}"
            body = f"Hello Admin,\n\nFrom: {username}\nEmail: {client_gmail}\nMessage: {data_field}"
            
            # Send the email
            email_sent = send_email_smtp(gmail, subject, username, body)
            
            # Check if the email was sent successfully
            if email_sent:
                return JsonResponse({'message': 'Email sent successfully!'}, status=200)
            else:
                return JsonResponse({'error': 'Failed to send email'}, status=500)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)



def get_admin_response(request):
    # Ensure the request method is GET
    if request.method == "GET":
        # Check if the user is logged in by looking for the username in the session
        username = request.session.get('username')
        if not username:
            return JsonResponse({"error": "User not logged in"}, status=403)

        # Get the latest ClientMessage for the logged-in user
        last_message = ClientMessage.objects.filter(name=username).order_by('-id').first()

        if not last_message:
            return JsonResponse({"error": "No messages found for this user"}, status=404)

        # Check if msg_info is None (equivalent to null in Python)
        if last_message.msg_info is None:
            response = {
                "admin_response": last_message.admin_response,
                "message_info": '-admin still need to respond-',
            }
        else:
            response = {
                "admin_response": last_message.admin_response,
                "message_info": last_message.msg_info,
            }

        # Return the response with admin_response and message_info
        return JsonResponse(response, status=200)

    # Return an error if the request method is not GET
    return JsonResponse({"error": "Invalid request method"}, status=405)



def post_user_message(request):
    # Ensure the request method is POST
    if request.method == "POST":
        try:
            # Parse the JSON data from the request body
            data = json.loads(request.body)

            # Extract 'userName' and 'message' from the payload
            name = data.get('userName')
            message_info = data.get('message')

            # Validate required fields
            if not name:
                return JsonResponse({"error": "Username is required."}, status=400)
            if not message_info:
                return JsonResponse({"error": "Message content is required."}, status=400)

            # Validate CSRF token (if applicable in your app)
            csrf_token_key = request.headers.get('X-Custom-CSRFToken')
            if not csrf_token_key:
                return JsonResponse({"error": "CSRF token is missing."}, status=400)

            session_result = find_session_by_csrf_token_key(csrf_token_key)  # Your custom CSRF validation logic
            if not session_result:
                return JsonResponse({'error': 'Invalid or expired CSRF token key.'}, status=403)

            # Fetch the user's email based on the username
            gmail = get_user_email_by_username(name)
            if not gmail:
                return JsonResponse({"error": f"No email found for username '{name}'."}, status=404)

            # Save the message to the database
            new_message = ClientMessage(
                name=name,  # The username
                msg_info=message_info,  # The message content
                gmail=gmail,  # The user's email
                is_client=True  # Assuming this is for client messages
            )
            new_message.save()

            # Respond with a success message
            return JsonResponse({
                "message": "Your message has been sent to the admin. We will respond shortly.",
                "message_info": new_message.msg_info,
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format."}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"An unexpected error occurred: {str(e)}"}, status=500)

    # Return an error if the request method is not POST
    return JsonResponse({"error": "Invalid request method. Only POST is allowed."}, status=405)


