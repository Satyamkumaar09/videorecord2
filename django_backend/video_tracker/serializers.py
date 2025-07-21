from rest_framework import serializers
from .models import VideoSession, LocationData, FrameAnalysis

class LocationDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationData
        fields = ['latitude', 'longitude', 'altitude', 'accuracy', 
                 'timestamp', 'frame_start', 'frame_end', 'address']

class FrameAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = FrameAnalysis
        fields = ['frame_number', 'timestamp', 'garbage_detected', 
                 'confidence_score', 'latitude', 'longitude']

class VideoSessionSerializer(serializers.ModelSerializer):
    locations = LocationDataSerializer(many=True, read_only=True)
    frame_analyses = FrameAnalysisSerializer(many=True, read_only=True)
    duration_seconds = serializers.SerializerMethodField()
    location_count = serializers.SerializerMethodField()
    
    class Meta:
        model = VideoSession
        fields = ['session_id', 'video_filename', 'start_time', 'end_time', 
                 'total_frames', 'fps', 'location_update_interval', 
                 'upload_status', 'yolo_processed', 'garbage_detected',
                 'processing_status', 'created_at', 'duration_seconds', 
                 'location_count', 'locations', 'frame_analyses']
    
    def get_duration_seconds(self, obj):
        if obj.end_time and obj.start_time:
            return (obj.end_time - obj.start_time) // 1000
        return 0
    
    def get_location_count(self, obj):
        return obj.locations.count()