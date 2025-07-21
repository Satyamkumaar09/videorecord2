# Add these to your existing Django settings.py

INSTALLED_APPS = [
    # ... your existing apps ...
    'rest_framework',
    'corsheaders',
    'video_tracker',  # Your new app for handling video uploads
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    # ... your existing middleware ...
]

# CORS settings (for development - make more restrictive in production)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # If you have a frontend
    "http://127.0.0.1:3000",
]

CORS_ALLOW_ALL_ORIGINS = True  # Only for development
CORS_ALLOW_CREDENTIALS = True

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # Change in production
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

# Media files settings (for video uploads)
import os
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100MB