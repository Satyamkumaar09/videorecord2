# Video Frame Upload API

A Django REST API for uploading video frames and metadata. This API is designed to receive video frames (images) along with JSON metadata containing location information for frames 0-29.

## Features

- Upload multiple video frames with metadata in a single request
- Store metadata with location data for frames 0-29 (same location for all)
- Upload additional frames to existing sessions
- Retrieve session information, frames, and metadata
- Admin interface for managing sessions
- Validation for frame locations and image formats

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run migrations:
```bash
python manage.py migrate
```

3. Create a superuser (optional):
```bash
python manage.py createsuperuser
```

4. Start the development server:
```bash
python manage.py runserver
```

## API Endpoints

### 1. Upload Video with Metadata
Upload video frames along with metadata in a single request.

**Endpoint:** `POST /api/video/sessions/upload_video_with_metadata/`

**Content-Type:** `multipart/form-data`

**Parameters:**
- `session_name` (optional): Name for the video session
- `metadata`: JSON string containing video metadata
- `frame_locations`: JSON string with location data for frames 0-29
- `frames`: List of image files

**Example:**
```python
import requests
import json

files = [
    ('frames', ('frame_0.jpg', open('frame_0.jpg', 'rb'), 'image/jpeg')),
    ('frames', ('frame_1.jpg', open('frame_1.jpg', 'rb'), 'image/jpeg')),
]

data = {
    'session_name': 'My Video Session',
    'metadata': json.dumps({
        "video_info": {"fps": 30, "duration": 1.0},
        "device": "camera_1"
    }),
    'frame_locations': json.dumps({
        "0": {"x": 100, "y": 200, "width": 640, "height": 480},
        "1": {"x": 100, "y": 200, "width": 640, "height": 480},
        # ... locations for frames 0-29
    })
}

response = requests.post('http://localhost:8000/api/video/sessions/upload_video_with_metadata/', 
                        data=data, files=files)
```

### 2. Upload Additional Frames
Add more frames to an existing session.

**Endpoint:** `POST /api/video/sessions/{session_id}/upload_frames/`

**Parameters:**
- `frames`: List of image files
- `start_frame_number`: Starting frame number (default: 0)

### 3. Upload/Update Metadata
Upload or update metadata for an existing session.

**Endpoint:** `POST /api/video/sessions/{session_id}/upload_metadata/`

**Content-Type:** `application/json`

**Parameters:**
- `metadata_json`: JSON object with metadata
- `frame_locations`: JSON object with location data for frames 0-29

### 4. Get Session Information
Retrieve information about a specific session.

**Endpoint:** `GET /api/video/sessions/{session_id}/`

### 5. Get Session Frames
Retrieve all frames for a session.

**Endpoint:** `GET /api/video/sessions/{session_id}/frames/`

### 6. Get Session Metadata
Retrieve metadata for a session.

**Endpoint:** `GET /api/video/sessions/{session_id}/metadata/`

### 7. List All Sessions
Get a list of all video sessions.

**Endpoint:** `GET /api/video/sessions/`

## Frame Location Format

The `frame_locations` parameter must contain location data for frames 0-29. Each frame location should have the following structure:

```json
{
  "0": {"x": 100, "y": 200, "width": 640, "height": 480},
  "1": {"x": 100, "y": 200, "width": 640, "height": 480},
  ...
  "29": {"x": 100, "y": 200, "width": 640, "height": 480}
}
```

## Supported Image Formats

- JPEG (.jpg, .jpeg)
- PNG (.png)
- BMP (.bmp)

## Testing

Run the example test script:

```bash
python examples/test_api.py
```

This will create test images and demonstrate all API endpoints.

## Models

### VideoSession
- `id`: Primary key
- `name`: Optional session name
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp
- `total_frames`: Number of frames in the session

### VideoFrame
- `id`: Primary key
- `session`: Foreign key to VideoSession
- `frame_number`: Frame sequence number
- `image`: Uploaded image file
- `uploaded_at`: Upload timestamp

### FrameMetadata
- `id`: Primary key
- `session`: One-to-one relationship with VideoSession
- `metadata_json`: JSON metadata
- `frame_locations`: JSON with location data for frames 0-29
- `uploaded_at`: Upload timestamp

## Admin Interface

Access the admin interface at `/admin/` to manage sessions, frames, and metadata.

## Configuration

Key settings in `settings.py`:

```python
# File upload limits
FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```