from django.db import models
import uuid

class VideoSession(models.Model):
    session_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    video_filename = models.CharField(max_length=255)
    video_file = models.FileField(upload_to='videos/', null=True, blank=True)
    start_time = models.BigIntegerField()  # Timestamp in milliseconds
    end_time = models.BigIntegerField(null=True, blank=True)
    total_frames = models.IntegerField(default=0)
    fps = models.IntegerField(default=30)
    location_update_interval = models.IntegerField(default=30)
    upload_status = models.CharField(max_length=50, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # YOLO processing status
    yolo_processed = models.BooleanField(default=False)
    garbage_detected = models.BooleanField(default=False)
    processing_status = models.CharField(max_length=50, default='pending')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Session {self.session_id} - {self.video_filename}"

class LocationData(models.Model):
    session = models.ForeignKey(VideoSession, on_delete=models.CASCADE, related_name='locations')
    latitude = models.FloatField()
    longitude = models.FloatField()
    altitude = models.FloatField(null=True, blank=True)
    accuracy = models.FloatField(null=True, blank=True)
    timestamp = models.BigIntegerField()  # GPS timestamp in milliseconds
    frame_start = models.IntegerField()
    frame_end = models.IntegerField()
    address = models.CharField(max_length=500, null=True, blank=True)
    
    class Meta:
        ordering = ['frame_start']
    
    def __str__(self):
        return f"Location for frames {self.frame_start}-{self.frame_end}"

class FrameAnalysis(models.Model):
    """Store YOLO analysis results for each frame"""
    session = models.ForeignKey(VideoSession, on_delete=models.CASCADE, related_name='frame_analyses')
    frame_number = models.IntegerField()
    timestamp = models.BigIntegerField()  # Frame timestamp
    
    # YOLO detection results
    garbage_detected = models.BooleanField(default=False)
    confidence_score = models.FloatField(null=True, blank=True)
    detection_data = models.JSONField(null=True, blank=True)  # Store full YOLO results
    
    # Location data for this frame (derived from LocationData)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    class Meta:
        ordering = ['frame_number']
        unique_together = ['session', 'frame_number']
    
    def __str__(self):
        return f"Frame {self.frame_number} - Garbage: {self.garbage_detected}"