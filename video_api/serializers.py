from rest_framework import serializers
from .models import VideoSession, VideoFrame, FrameMetadata


class VideoSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoSession
        fields = ['id', 'name', 'created_at', 'updated_at', 'total_frames']
        read_only_fields = ['id', 'created_at', 'updated_at', 'total_frames']


class VideoFrameSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoFrame
        fields = ['id', 'session', 'frame_number', 'image', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']


class FrameMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = FrameMetadata
        fields = ['id', 'session', 'metadata_json', 'frame_locations', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']


class VideoUploadSerializer(serializers.Serializer):
    """
    Serializer for handling bulk video frame uploads with metadata
    """
    session_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    metadata = serializers.JSONField()
    frame_locations = serializers.JSONField()
    frames = serializers.ListField(
        child=serializers.ImageField(),
        allow_empty=False,
        max_length=100  # Limit to 100 frames per upload
    )
    
    def validate_frame_locations(self, value):
        """
        Validate that frame_locations contains data for frames 0-29
        """
        if not isinstance(value, dict):
            raise serializers.ValidationError("Frame locations must be a dictionary")
        
        # Check if we have location data for frames 0-29
        expected_frames = set(str(i) for i in range(30))
        provided_frames = set(value.keys())
        
        if not expected_frames.issubset(provided_frames):
            missing_frames = expected_frames - provided_frames
            raise serializers.ValidationError(f"Missing location data for frames: {sorted(missing_frames)}")
        
        return value
    
    def validate_frames(self, value):
        """
        Validate uploaded frames
        """
        if len(value) == 0:
            raise serializers.ValidationError("At least one frame is required")
        
        # Check file types
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/bmp']
        for i, frame in enumerate(value):
            if hasattr(frame, 'content_type') and frame.content_type not in allowed_types:
                raise serializers.ValidationError(f"Frame {i}: Invalid file type. Allowed types: {allowed_types}")
        
        return value


class SessionFramesUploadSerializer(serializers.Serializer):
    """
    Serializer for uploading frames to an existing session
    """
    frames = serializers.ListField(
        child=serializers.ImageField(),
        allow_empty=False,
        max_length=100
    )
    start_frame_number = serializers.IntegerField(min_value=0, default=0)
    
    def validate_frames(self, value):
        """
        Validate uploaded frames
        """
        if len(value) == 0:
            raise serializers.ValidationError("At least one frame is required")
        
        # Check file types
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/bmp']
        for i, frame in enumerate(value):
            if hasattr(frame, 'content_type') and frame.content_type not in allowed_types:
                raise serializers.ValidationError(f"Frame {i}: Invalid file type. Allowed types: {allowed_types}")
        
        return value
