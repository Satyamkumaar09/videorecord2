from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import logging

from garbage_detection.models import VideoSession, LocationData
from garbage_detection.yolo_processor import process_video_async
from .serializers import VideoSessionSerializer, LocationDataSerializer

logger = logging.getLogger(__name__)

@csrf_exempt
@api_view(['POST'])
@parser_classes([JSONParser])
@permission_classes([AllowAny])
def upload_location_data(request):
    """
    Accept location data from Android app
    
    Expected JSON format:
    {
        "session_id": "uuid",
        "video_filename": "VID_20241214_143022.mp4",
        "start_time": 1702565422000,
        "end_time": 1702565482000,
        "total_frames": 1800,
        "fps": 30,
        "location_update_interval": 30,
        "locations": [
            {
                "latitude": 37.7749,
                "longitude": -122.4194,
                "altitude": 52.3,
                "accuracy": 4.2,
                "timestamp": 1702565422000,
                "frame_start": 0,
                "frame_end": 29
            }
        ]
    }
    """
    try:
        data = request.data
        logger.info(f"Received location data for session: {data.get('session_id')}")
        
        # Validate required fields
        required_fields = ['session_id', 'video_filename', 'start_time', 'total_frames', 'fps', 'locations']
        for field in required_fields:
            if field not in data:
                return Response({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate duration
        duration_ms = data.get('end_time', data['start_time']) - data['start_time']
        duration_seconds = max(1, duration_ms // 1000)
        
        # Create or get video session
        session, created = VideoSession.objects.get_or_create(
            session_id=data['session_id'],
            defaults={
                'video_filename': data['video_filename'],
                'start_time': data['start_time'],
                'end_time': data.get('end_time', data['start_time']),
                'total_frames': data['total_frames'],
                'fps': data['fps'],
                'duration_seconds': duration_seconds,
                'location_update_interval': data.get('location_update_interval', 30),
                'upload_status': 'location_uploaded'
            }
        )
        
        if not created:
            # Update existing session
            session.end_time = data.get('end_time', session.end_time)
            session.total_frames = data['total_frames']
            session.duration_seconds = duration_seconds
            session.location_update_interval = data.get('location_update_interval', session.location_update_interval)
            session.upload_status = 'location_uploaded'
            # Clear existing location data
            session.locations.all().delete()
            session.save()
        
        # Create location data entries
        location_objects = []
        for loc_data in data['locations']:
            # Validate location data
            if not all(key in loc_data for key in ['latitude', 'longitude', 'frame_start', 'frame_end']):
                continue
                
            location_objects.append(LocationData(
                session=session,
                latitude=loc_data['latitude'],
                longitude=loc_data['longitude'],
                altitude=loc_data.get('altitude'),
                accuracy=loc_data.get('accuracy'),
                timestamp=loc_data.get('timestamp', data['start_time']),
                frame_start=loc_data['frame_start'],
                frame_end=loc_data['frame_end'],
                address=loc_data.get('address')
            ))
        
        # Bulk create location data
        if location_objects:
            LocationData.objects.bulk_create(location_objects)
            logger.info(f"Created {len(location_objects)} location entries for session {session.session_id}")
        
        return Response({
            'success': True,
            'message': 'Location data uploaded successfully',
            'session_id': str(session.session_id),
            'locations_count': len(location_objects)
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error uploading location data: {e}")
        return Response({
            'success': False,
            'message': f'Error uploading location data: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['POST'])
@parser_classes([MultiPartParser])
@permission_classes([AllowAny])
def upload_video(request):
    """
    Accept video file from Android app
    
    Form data:
    - session_id: UUID string
    - video: Video file
    """
    try:
        session_id = request.data.get('session_id')
        video_file = request.FILES.get('video')
        
        logger.info(f"Received video upload for session: {session_id}")
        
        if not session_id:
            return Response({
                'success': False,
                'message': 'Missing session_id'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not video_file:
            return Response({
                'success': False,
                'message': 'Missing video file'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate file type
        if not video_file.content_type.startswith('video/'):
            return Response({
                'success': False,
                'message': 'File must be a video'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get or create session
        try:
            session = VideoSession.objects.get(session_id=session_id)
        except VideoSession.DoesNotExist:
            # Create session if it doesn't exist (video uploaded before location data)
            session = VideoSession.objects.create(
                session_id=session_id,
                video_filename=video_file.name,
                start_time=int(timezone.now().timestamp() * 1000),
                upload_status='video_uploaded'
            )
        
        # Save video file
        session.video_file = video_file
        session.video_filename = video_file.name
        
        # Update upload status
        if session.locations.exists():
            session.upload_status = 'complete'
        else:
            session.upload_status = 'video_uploaded'
        
        session.save()
        
        # Trigger YOLO processing if we have both video and location data
        if session.upload_status == 'complete' and session.processing_status == 'pending':
            logger.info(f"Triggering YOLO processing for session {session.session_id}")
            process_video_async.delay(session.id)
        
        logger.info(f"Video uploaded successfully for session {session.session_id}")
        
        return Response({
            'success': True,
            'message': 'Video uploaded successfully',
            'session_id': str(session.session_id),
            'file_url': request.build_absolute_uri(session.video_file.url) if session.video_file else None,
            'processing_status': session.processing_status
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error uploading video: {e}")
        return Response({
            'success': False,
            'message': f'Error uploading video: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_sessions(request):
    """
    Get all video sessions with summary information
    """
    try:
        sessions = VideoSession.objects.all().order_by('-created_at')
        
        # Apply filters if provided
        status_filter = request.GET.get('status')
        if status_filter:
            sessions = sessions.filter(processing_status=status_filter)
        
        garbage_filter = request.GET.get('garbage_detected')
        if garbage_filter is not None:
            garbage_detected = garbage_filter.lower() == 'true'
            sessions = sessions.filter(garbage_detected=garbage_detected)
        
        serializer = VideoSessionSerializer(sessions, many=True, context={'request': request})
        
        return Response({
            'success': True,
            'count': sessions.count(),
            'sessions': serializer.data
        })
        
    except Exception as e:
        logger.error(f"Error fetching sessions: {e}")
        return Response({
            'success': False,
            'message': f'Error fetching sessions: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_session_details(request, session_id):
    """
    Get detailed session data including locations and detection results
    """
    try:
        session = VideoSession.objects.get(session_id=session_id)
        
        # Get location data
        locations = session.locations.all()
        location_serializer = LocationDataSerializer(locations, many=True)
        
        # Get detection results summary
        detections = session.detections.filter(garbage_detected=True)
        detection_summary = {
            'total_detections': detections.count(),
            'garbage_types': list(detections.values_list('garbage_type', flat=True).distinct()),
            'severity_levels': list(detections.values_list('severity_level', flat=True).distinct()),
            'confidence_avg': detections.aggregate(avg_conf=models.Avg('confidence_score'))['avg_conf']
        }
        
        # Get garbage locations
        garbage_locations = session.detections.filter(
            garbage_detected=True
        ).values(
            'latitude', 'longitude', 'garbage_type', 'severity_level', 'confidence_score'
        ).distinct()
        
        session_serializer = VideoSessionSerializer(session, context={'request': request})
        
        response_data = session_serializer.data
        response_data.update({
            'locations': location_serializer.data,
            'detection_summary': detection_summary,
            'garbage_locations': list(garbage_locations)
        })
        
        return Response({
            'success': True,
            'session': response_data
        })
        
    except VideoSession.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Session not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error fetching session details: {e}")
        return Response({
            'success': False,
            'message': f'Error fetching session details: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def trigger_processing(request, session_id):
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
        
        if session.processing_status == 'processing':
            return Response({
                'success': False,
                'message': 'Session is already being processed'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Reset processing status and trigger processing
        session.processing_status = 'pending'
        session.yolo_processed = False
        session.save()
        
        # Trigger async processing
        task = process_video_async.delay(session.id)
        
        logger.info(f"Manual processing triggered for session {session.session_id}")
        
        return Response({
            'success': True,
            'message': 'Processing triggered successfully',
            'task_id': task.id,
            'session_id': str(session.session_id)
        })
        
    except VideoSession.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Session not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error triggering processing: {e}")
        return Response({
            'success': False,
            'message': f'Error triggering processing: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint for Android app
    """
    return Response({
        'status': 'healthy',
        'message': 'Smart City Garbage Detection API',
        'timestamp': timezone.now().isoformat(),
        'version': '1.0.0'
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def api_stats(request):
    """
    Get API statistics
    """
    try:
        from django.db.models import Count, Avg
        
        stats = {
            'total_sessions': VideoSession.objects.count(),
            'processed_sessions': VideoSession.objects.filter(yolo_processed=True).count(),
            'sessions_with_garbage': VideoSession.objects.filter(garbage_detected=True).count(),
            'processing_status_breakdown': VideoSession.objects.values('processing_status').annotate(
                count=Count('processing_status')
            ),
            'total_detections': session.detections.filter(garbage_detected=True).count(),
            'avg_confidence': session.detections.filter(garbage_detected=True).aggregate(
                avg=Avg('confidence_score')
            )['avg']
        }
        
        return Response({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return Response({
            'success': False,
            'message': f'Error fetching stats: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)