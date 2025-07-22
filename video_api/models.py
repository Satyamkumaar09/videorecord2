from django.db import models
import json
from django.core.exceptions import ValidationError


class VideoSession(models.Model):
    """
    Represents a video recording session
    """
    name = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    total_frames = models.IntegerField(default=0)
    
    def __str__(self):
        return f"Video Session {self.id} - {self.name or 'Unnamed'}"


class VideoFrame(models.Model):
    """
    Stores individual video frames
    """
    session = models.ForeignKey(VideoSession, on_delete=models.CASCADE, related_name='frames')
    frame_number = models.IntegerField()
    image = models.ImageField(upload_to='video_frames/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('session', 'frame_number')
        ordering = ['frame_number']
    
    def __str__(self):
        return f"Frame {self.frame_number} - Session {self.session.id}"


class FrameMetadata(models.Model):
    """
    Stores metadata for video frames
    """
    session = models.OneToOneField(VideoSession, on_delete=models.CASCADE, related_name='metadata')
    metadata_json = models.JSONField()
    frame_locations = models.JSONField()  # Will store location data for frames 0-29
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def clean(self):
        """
        Validate that frame_locations contains data for frames 0-29
        """
        if self.frame_locations:
            if not isinstance(self.frame_locations, dict):
                raise ValidationError("Frame locations must be a dictionary")
            
            # Check if we have location data for frames 0-29
            expected_frames = set(str(i) for i in range(30))
            provided_frames = set(self.frame_locations.keys())
            
            if not expected_frames.issubset(provided_frames):
                missing_frames = expected_frames - provided_frames
                raise ValidationError(f"Missing location data for frames: {sorted(missing_frames)}")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Metadata for Session {self.session.id}"
