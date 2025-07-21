from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.response import Response
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
import json
import uuid
from .models import VideoSession, LocationData, FrameAnalysis
from .serializers import VideoSessionSerializer, LocationDataSerializer
from .yolo_processor import process_video_with_yolo  # Your existing YOLO function
from django.utils import timezone

@csrf_exempt
@api_view(['POST'])
@parser_classes([JSONParser])
def upload_location_data(request):
    """
    Accept location data from Android app
    """
    try:
        data = request.data
        
        # Create or get video session
        session, created = VideoSession.objects.get_or_create(
            session_id=data['session_id'],
            defaults={
                'video_filename': data['video_filename'],
                'start_time': data['start_time'],
                'end_time': data['end_time'],
                'total_frames': data['total_frames'],
                'fps': data['fps'],
                'location_update_interval': data['location_update_interval'],
                'upload_status': 'location_uploaded'
            }
        )
        
        # Clear existing location data if updating
        if not created:
            session.locations.all().delete()
            session.end_time = data['end_time']
            session.total_frames = data['total_frames']
            session.save()
        
        # Create location data entries
        location_objects = []
        for loc_data in data['locations']:
            location_objects.append(LocationData(
                session=session,
                latitude=loc_data['latitude'],
                longitude=loc_data['longitude'],
                altitude=loc_data.get('altitude'),
                accuracy=loc_data.get('accuracy'),
                timestamp=loc_data['timestamp'],
                frame_start=loc_data['frame_start'],
                frame_end=loc_data['frame_end'],
                address=loc_data.get('address')
            ))
        
        LocationData.objects.bulk_create(location_objects)
        
        return Response({
            'success': True,
            'message': 'Location data uploaded successfully',
            'session_id': str(session.session_id)
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error uploading location data: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
@api_view(['POST'])
@parser_classes([MultiPartParser])
def upload_video(request):
    """
    Accept video file from Android app
    """
    try:
        session_id = request.data.get('session_id')
        video_file = request.FILES.get('video')
        
        if not session_id or not video_file:
            return Response({
                'success': False,
                'message': 'Missing session_id or video file'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get or create session
        session, created = VideoSession.objects.get_or_create(
            session_id=session_id,
            defaults={
                'video_filename': video_file.name,
                'start_time': int(timezone.now().timestamp() * 1000),
                'upload_status': 'video_uploaded'
            }
        )
        
        # Save video file
        session.video_file = video_file
        session.video_filename = video_file.name
        session.upload_status = 'complete'
        session.save()
        
        # Trigger YOLO processing asynchronously
        process_video_async.delay(session.id)  # Using Celery (optional)
        # OR process immediately: process_video_with_yolo(session)
        
        return Response({
            'success': True,
            'message': 'Video uploaded successfully',
            'session_id': str(session.session_id),
            'file_url': request.build_absolute_uri(session.video_file.url) if session.video_file else None
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error uploading video: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_sessions(request):
    """
    Get all video sessions
    """
    sessions = VideoSession.objects.all()
    serializer = VideoSessionSerializer(sessions, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_session_details(request, session_id):
    """
    Get detailed session data including locations and YOLO results
    """
    try:
        session = VideoSession.objects.get(session_id=session_id)
        
        # Get location data
        locations = LocationData.objects.filter(session=session)
        location_data = LocationDataSerializer(locations, many=True).data
        
        # Get YOLO results
        frame_analyses = FrameAnalysis.objects.filter(session=session)
        
        response_data = {
            'session_id': str(session.session_id),
            'video_filename': session.video_filename,
            'start_time': session.start_time,
            'end_time': session.end_time,
            'total_frames': session.total_frames,
            'fps': session.fps,
            'location_update_interval': session.location_update_interval,
            'locations': location_data,
            'yolo_processed': session.yolo_processed,
            'garbage_detected': session.garbage_detected,
            'frame_analyses': [
                {
                    'frame_number': fa.frame_number,
                    'garbage_detected': fa.garbage_detected,
                    'confidence_score': fa.confidence_score,
                    'latitude': fa.latitude,
                    'longitude': fa.longitude,
                } for fa in frame_analyses
            ]
        }
        
        return Response(response_data)
        
    except VideoSession.DoesNotExist:
        return Response({
            'error': 'Session not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def process_video(request, session_id):
    """
    Manually trigger YOLO processing for a session
    """
    try:
        session = VideoSession.objects.get(session_id=session_id)
        
        if not session.video_file:
            return Response({
                'success': False,
                'message': 'No video file found for this session'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Process with your existing YOLO model
        results = process_video_with_yolo(session)
        
        return Response({
            'success': True,
            'message': 'Video processing completed',
            'results': results
        })
        
    except VideoSession.DoesNotExist:
        return Response({
            'error': 'Session not found'
        }, status=status.HTTP_404_NOT_FOUND)

# Integration with your existing YOLO processing
def process_video_with_yolo(session):
    """
    Process video with your existing YOLO model
    Integrate this with your current YOLO processing code
    """
    try:
        session.processing_status = 'processing'
        session.save()
        
        # Your existing YOLO code here
        # Example integration:
        video_path = session.video_file.path
        
        # Get location data for frame mapping
        locations = session.locations.all()
        location_map = {}
        for loc in locations:
            for frame_num in range(loc.frame_start, loc.frame_end + 1):
                location_map[frame_num] = {
                    'latitude': loc.latitude,
                    'longitude': loc.longitude
                }
        
        # Process video frames with YOLO (your existing code)
        # frame_results = your_yolo_function(video_path)
        
        # Store results in database
        frame_analyses = []
        garbage_found = False
        
        # Example - replace with your actual YOLO results
        for frame_num in range(session.total_frames):
            # yolo_result = process_frame_with_yolo(frame_num)  # Your function
            
            # Example result structure
            garbage_detected = False  # Replace with actual YOLO result
            confidence = 0.0  # Replace with actual confidence
            
            if garbage_detected:
                garbage_found = True
            
            location = location_map.get(frame_num, {})
            
            frame_analyses.append(FrameAnalysis(
                session=session,
                frame_number=frame_num,
                timestamp=session.start_time + (frame_num * (1000 // session.fps)),
                garbage_detected=garbage_detected,
                confidence_score=confidence,
                latitude=location.get('latitude'),
                longitude=location.get('longitude'),
                detection_data={}  # Store full YOLO results here
            ))
        
        # Bulk create frame analyses
        FrameAnalysis.objects.bulk_create(frame_analyses)
        
        # Update session status
        session.yolo_processed = True
        session.garbage_detected = garbage_found
        session.processing_status = 'completed'
        session.save()
        
        return {
            'frames_processed': len(frame_analyses),
            'garbage_detected': garbage_found
        }
        
    except Exception as e:
        session.processing_status = 'failed'
        session.save()
        raise e

# Optional: Async processing with Celery
# @shared_task
# def process_video_async(session_id):
#     session = VideoSession.objects.get(id=session_id)
#     return process_video_with_yolo(session)