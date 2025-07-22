from django.shortcuts import render
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db import transaction
from .models import VideoSession, VideoFrame, FrameMetadata
from .serializers import (
    VideoSessionSerializer, 
    VideoFrameSerializer, 
    FrameMetadataSerializer,
    VideoUploadSerializer,
    SessionFramesUploadSerializer
)


class VideoSessionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing video sessions
    """
    queryset = VideoSession.objects.all()
    serializer_class = VideoSessionSerializer
    
    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_video_with_metadata(self, request):
        """
        Upload video frames with metadata in a single request.
        
        Expected data:
        - session_name (optional): Name for the session
        - metadata: JSON metadata for the session
        - frame_locations: JSON with location data for frames 0-29
        - frames: List of image files
        """
        serializer = VideoUploadSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    # Create video session
                    session = VideoSession.objects.create(
                        name=serializer.validated_data.get('session_name', '')
                    )
                    
                    # Save metadata
                    FrameMetadata.objects.create(
                        session=session,
                        metadata_json=serializer.validated_data['metadata'],
                        frame_locations=serializer.validated_data['frame_locations']
                    )
                    
                    # Save frames
                    frames = serializer.validated_data['frames']
                    frame_objects = []
                    
                    for i, frame_file in enumerate(frames):
                        frame_obj = VideoFrame(
                            session=session,
                            frame_number=i,
                            image=frame_file
                        )
                        frame_objects.append(frame_obj)
                    
                    VideoFrame.objects.bulk_create(frame_objects)
                    
                    # Update session with total frames
                    session.total_frames = len(frames)
                    session.save()
                    
                    return Response({
                        'message': 'Video uploaded successfully',
                        'session_id': session.id,
                        'total_frames': len(frames)
                    }, status=status.HTTP_201_CREATED)
                    
            except Exception as e:
                return Response({
                    'error': f'Failed to upload video: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_frames(self, request, pk=None):
        """
        Upload additional frames to an existing session
        """
        try:
            session = self.get_object()
            serializer = SessionFramesUploadSerializer(data=request.data)
            
            if serializer.is_valid():
                frames = serializer.validated_data['frames']
                start_frame_number = serializer.validated_data['start_frame_number']
                
                frame_objects = []
                for i, frame_file in enumerate(frames):
                    frame_number = start_frame_number + i
                    
                    # Check if frame number already exists
                    if VideoFrame.objects.filter(session=session, frame_number=frame_number).exists():
                        return Response({
                            'error': f'Frame {frame_number} already exists for this session'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    frame_obj = VideoFrame(
                        session=session,
                        frame_number=frame_number,
                        image=frame_file
                    )
                    frame_objects.append(frame_obj)
                
                VideoFrame.objects.bulk_create(frame_objects)
                
                # Update total frames count
                session.total_frames = session.frames.count()
                session.save()
                
                return Response({
                    'message': f'Uploaded {len(frames)} frames successfully',
                    'session_id': session.id,
                    'total_frames': session.total_frames
                }, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'error': f'Failed to upload frames: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], parser_classes=[JSONParser])
    def upload_metadata(self, request, pk=None):
        """
        Upload or update metadata for an existing session
        """
        try:
            session = self.get_object()
            serializer = FrameMetadataSerializer(data=request.data)
            
            if serializer.is_valid():
                # Check if metadata already exists
                if hasattr(session, 'metadata'):
                    # Update existing metadata
                    metadata = session.metadata
                    metadata.metadata_json = serializer.validated_data['metadata_json']
                    metadata.frame_locations = serializer.validated_data['frame_locations']
                    metadata.save()
                else:
                    # Create new metadata
                    FrameMetadata.objects.create(
                        session=session,
                        metadata_json=serializer.validated_data['metadata_json'],
                        frame_locations=serializer.validated_data['frame_locations']
                    )
                
                return Response({
                    'message': 'Metadata uploaded successfully',
                    'session_id': session.id
                }, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'error': f'Failed to upload metadata: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def frames(self, request, pk=None):
        """
        Get all frames for a session
        """
        session = self.get_object()
        frames = session.frames.all()
        serializer = VideoFrameSerializer(frames, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def metadata(self, request, pk=None):
        """
        Get metadata for a session
        """
        session = self.get_object()
        if hasattr(session, 'metadata'):
            serializer = FrameMetadataSerializer(session.metadata)
            return Response(serializer.data)
        else:
            return Response({
                'error': 'No metadata found for this session'
            }, status=status.HTTP_404_NOT_FOUND)
