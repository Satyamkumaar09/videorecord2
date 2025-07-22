#!/bin/bash

# Example curl commands for testing the Video Frame Upload API

echo "Starting Django server in background..."
python3 manage.py runserver &
SERVER_PID=$!

# Wait for server to start
sleep 3

echo "Testing API endpoints..."

# Create some test images
echo "Creating test images..."
mkdir -p test_images
for i in {0..4}; do
    # Create a simple colored rectangle as test image
    convert -size 640x480 xc:"rgb($(($i*50)),100,150)" test_images/frame_$i.jpg 2>/dev/null || {
        # Fallback if ImageMagick is not available
        echo "Creating placeholder for frame_$i.jpg"
        echo "Frame $i placeholder" > test_images/frame_$i.txt
    }
done

# Test 1: Upload video with metadata
echo -e "\n1. Testing video upload with metadata..."

# Create frame locations JSON (same location for frames 0-29)
FRAME_LOCATIONS='{'
for i in {0..29}; do
    if [ $i -gt 0 ]; then
        FRAME_LOCATIONS+=','
    fi
    FRAME_LOCATIONS+="\"$i\":{\"x\":100,\"y\":200,\"width\":640,\"height\":480}"
done
FRAME_LOCATIONS+='}'

# Create metadata JSON
METADATA='{"video_info":{"fps":30,"duration":1.0,"resolution":"640x480"},"recording_info":{"device":"test_camera","timestamp":"2024-01-01T12:00:00Z"}}'

# Upload video with metadata
curl -X POST http://localhost:8000/api/video/sessions/upload_video_with_metadata/ \
  -F "session_name=Test Video Session" \
  -F "metadata=$METADATA" \
  -F "frame_locations=$FRAME_LOCATIONS" \
  -F "frames=@test_images/frame_0.jpg" \
  -F "frames=@test_images/frame_1.jpg" \
  -F "frames=@test_images/frame_2.jpg" \
  -F "frames=@test_images/frame_3.jpg" \
  -F "frames=@test_images/frame_4.jpg" \
  -H "Accept: application/json"

echo -e "\n\n2. Testing session list..."
curl -X GET http://localhost:8000/api/video/sessions/ \
  -H "Accept: application/json"

echo -e "\n\n3. Testing session details (assuming session ID 1)..."
curl -X GET http://localhost:8000/api/video/sessions/1/ \
  -H "Accept: application/json"

echo -e "\n\n4. Testing session frames (assuming session ID 1)..."
curl -X GET http://localhost:8000/api/video/sessions/1/frames/ \
  -H "Accept: application/json"

echo -e "\n\n5. Testing session metadata (assuming session ID 1)..."
curl -X GET http://localhost:8000/api/video/sessions/1/metadata/ \
  -H "Accept: application/json"

# Clean up
echo -e "\n\nCleaning up..."
kill $SERVER_PID
rm -rf test_images

echo -e "\nAPI testing completed!"
