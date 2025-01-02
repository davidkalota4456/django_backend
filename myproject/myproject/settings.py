
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
import os
from dotenv import load_dotenv
# Load environment variables from the .env file
load_dotenv()


# settings.py
APPEND_SLASH = False
#SESSION_COOKIE_AGE = 600  # 10 minutes
SESSION_COOKIE_AGE = int(os.getenv('SESSION_COOKIE_AGE', 600))  # Default to 600 if not set in .env


SESSION_ENGINE = 'django.contrib.sessions.backends.db'


# myproject/settings.py

# Now you can access the variables like this
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
BUCKET_NAME = os.getenv("BUCKET_NAME")
ENV_SENDER_EMAIL = os.getenv("ENV_SENDER_EMAIL")
ENV_PASSWORD = os.getenv("ENV_PASSWORD")



# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG') == 'True'


#ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')



# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'django.contrib.sessions',
    'myapp',
    'users',
    'user_admin',
    'clients_projects',
    'clients_msg',
    'corsheaders',
    'zoommeetings',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

#CORS_ALLOWED_ORIGINS = [
#    "http://localhost:3000" 
#]
CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', '').split(',')

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',  # Backend URL
    'http://localhost:3000',  # Frontend URL
]
CSRF_COOKIE_DOMAIN = None  
CORS_ALLOW_CREDENTIALS = True


ROOT_URLCONF = 'myproject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': False,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'myproject.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('RDS_SCHEMA_NAME'),  # Get schema name from .env
        'USER': os.getenv('RDS_USER'),        # Get user from .env
        'PASSWORD': os.getenv('RDS_PASSWORD'), # Get password from .env
        'HOST': os.getenv('RDS_HOST'),        # Get host from .env
        'PORT': os.getenv('PORT'),            # Get port from .env
    }
}


CSRF_COOKIE_NAME = None  # Default CSRF cookie name
CSRF_USE_SESSIONS = False
CSRF_COOKIE_SECURE = False  # Set to True only if using HTTPS
CSRF_COOKIE_HTTPONLY = False  # Set to False to access it via JavaScript
CSRF_COOKIE_PATH = '/'  # Should be available on all paths
#CORS_ALLOW_CREDENTIALS = True
CSRF_COOKIE_SAMESITE = 'None'
# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
CSRF_HEADER_NAME = 'X-Custom-CSRFToken'  # This is the default name


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = [
    'X-Custom-CSRFToken',  # Add the custom CSRF token header
    'content-type',
    'accept',
    'authorization',
    # Add any other headers you might need
]
CSRF_HEADER_NAME = 'HTTP_X_CSRFTOKEN'
