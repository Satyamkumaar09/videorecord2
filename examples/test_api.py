#!/usr/bin/env python3
"""
Example script to test the video frame upload API
"""
import requests
import json
from io import BytesIO
from PIL import Image
import os

# API base URL
BASE_URL = 'http://localhost:8000/api/video'

def create_test_image(frame_number):
    """Create a simple test image"""
    img = Image.new('RGB', (640, 480), color=(frame_number * 10 % 255, 100, 150))
    # Add frame number text
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.load_default()
        draw.text((10, 10), f"Frame {frame_number}", fill=(255, 255, 255), font=font)
    except:
        draw.text((10, 10), f"Frame {frame_number}", fill=(255, 255, 255))
    
    # Convert to bytes
    buffer = BytesIO()
    img.save(buffer, format='JPEG')
    buffer.seek(0)
    return buffer

def test_upload_video_with_metadata():
    """Test uploading video frames with metadata"""
    
    # Create sample metadata
    metadata = {
        "video_info": {
            "fps": 30,
            "duration": 1.0,
            "resolution": "640x480"
        },
        "recording_info": {
            "device": "test_camera",
            "timestamp": "2024-01-01T12:00:00Z"
        }
    }
    
    # Create frame locations (same location for frames 0-29 as specified)
    frame_locations = {}
    for i in range(30):
        frame_locations[str(i)] = {
            "x": 100,
            "y": 200,
            "width": 640,
            "height": 480
        }
    
    # Prepare files for upload
    files = []
    for i in range(5):  # Upload 5 test frames
        img_buffer = create_test_image(i)
        files.append(('frames', (f'frame_{i}.jpg', img_buffer, 'image/jpeg')))
    
    # Prepare data
    data = {
        'session_name': 'Test Video Session',
        'metadata': json.dumps(metadata),
        'frame_locations': json.dumps(frame_locations)
    }
    
    # Make request
    url = f"{BASE_URL}/sessions/upload_video_with_metadata/"
    response = requests.post(url, data=data, files=files)
    
    print(f"Upload Response Status: {response.status_code}")
    print(f"Upload Response: {response.json()}")
    
    return response.json().get('session_id') if response.status_code == 201 else None

def test_upload_additional_frames(session_id):
    """Test uploading additional frames to existing session"""
    
    # Prepare additional frames
    files = []
    for i in range(5, 8):  # Upload frames 5-7
        img_buffer = create_test_image(i)
        files.append(('frames', (f'frame_{i}.jpg', img_buffer, 'image/jpeg')))
    
    data = {
        'start_frame_number': 5
    }
    
    url = f"{BASE_URL}/sessions/{session_id}/upload_frames/"
    response = requests.post(url, data=data, files=files)
    
    print(f"Additional Frames Response Status: {response.status_code}")
    print(f"Additional Frames Response: {response.json()}")

def test_get_session_info(session_id):
    """Test getting session information"""
    
    url = f"{BASE_URL}/sessions/{session_id}/"
    response = requests.get(url)
    
    print(f"Session Info Response Status: {response.status_code}")
    print(f"Session Info: {response.json()}")

def test_get_frames(session_id):
    """Test getting all frames for a session"""
    
    url = f"{BASE_URL}/sessions/{session_id}/frames/"
    response = requests.get(url)
    
    print(f"Frames Response Status: {response.status_code}")
    print(f"Number of frames: {len(response.json())}")

def test_get_metadata(session_id):
    """Test getting metadata for a session"""
    
    url = f"{BASE_URL}/sessions/{session_id}/metadata/"
    response = requests.get(url)
    
    print(f"Metadata Response Status: {response.status_code}")
    print(f"Metadata: {response.json()}")

if __name__ == "__main__":
    print("Testing Video Frame Upload API")
    print("=" * 40)
    
    # Test uploading video with metadata
    session_id = test_upload_video_with_metadata()
    
    if session_id:
        print(f"\nSession created with ID: {session_id}")
        
        # Test additional operations
        test_upload_additional_frames(session_id)
        test_get_session_info(session_id)
        test_get_frames(session_id)
        test_get_metadata(session_id)
    else:
        print("Failed to create session")
