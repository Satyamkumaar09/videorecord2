from django.contrib.gis.db import models
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
import uuid
from django.utils import timezone

class VideoSession(models.Model):
    """Video recording session from mobile app"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    session_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    video_filename = models.CharField(max_length=255)
    video_file = models.FileField(upload_to='videos/%Y/%m/%d/', null=True, blank=True)
    
    # Video metadata
    start_time = models.BigIntegerField()  # Timestamp in milliseconds
    end_time = models.BigIntegerField(null=True, blank=True)
    total_frames = models.IntegerField(default=0)
    fps = models.IntegerField(default=30)
    duration_seconds = models.IntegerField(default=0)
    
    # Location settings
    location_update_interval = models.IntegerField(default=30)  # frames
    
    # Processing status
    upload_status = models.CharField(max_length=50, default='pending')
    processing_status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    yolo_processed = models.BooleanField(default=False)
    
    # Results summary
    total_garbage_frames = models.IntegerField(default=0)
    garbage_detected = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # User who uploaded (if authentication added later)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['processing_status']),
            models.Index(fields=['garbage_detected']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Session {self.session_id} - {self.video_filename}"
    
    def get_duration_display(self):
        """Human readable duration"""
        if self.duration_seconds:
            minutes = self.duration_seconds // 60
            seconds = self.duration_seconds % 60
            return f"{minutes}m {seconds}s"
        return "0s"

class LocationData(models.Model):
    """GPS location data for frame ranges"""
    
    session = models.ForeignKey(VideoSession, on_delete=models.CASCADE, related_name='locations')
    
    # GPS coordinates
    latitude = models.FloatField()
    longitude = models.FloatField()
    altitude = models.FloatField(null=True, blank=True)
    accuracy = models.FloatField(null=True, blank=True)  # GPS accuracy in meters
    
    # Geographic point for spatial queries
    location = models.PointField(geography=True, null=True, blank=True)
    
    # Timing
    timestamp = models.BigIntegerField()  # GPS timestamp in milliseconds
    frame_start = models.IntegerField()
    frame_end = models.IntegerField()
    
    # Address (reverse geocoding)
    address = models.CharField(max_length=500, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    district = models.CharField(max_length=100, null=True, blank=True)
    
    class Meta:
        ordering = ['frame_start']
        indexes = [
            models.Index(fields=['session', 'frame_start']),
        ]
    
    def save(self, *args, **kwargs):
        # Create Point object for spatial queries
        if self.latitude and self.longitude:
            self.location = Point(self.longitude, self.latitude)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Location for frames {self.frame_start}-{self.frame_end}"

class GarbageDetection(models.Model):
    """YOLO detection results for individual frames"""
    
    GARBAGE_TYPES = [
        ('plastic_bottle', 'Plastic Bottle'),
        ('plastic_bag', 'Plastic Bag'),
        ('food_waste', 'Food Waste'),
        ('paper', 'Paper'),
        ('metal_can', 'Metal Can'),
        ('glass', 'Glass'),
        ('cigarette', 'Cigarette Butt'),
        ('other', 'Other Garbage'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    session = models.ForeignKey(VideoSession, on_delete=models.CASCADE, related_name='detections')
    frame_number = models.IntegerField()
    timestamp = models.BigIntegerField()  # Frame timestamp in milliseconds
    
    # YOLO detection results
    garbage_detected = models.BooleanField(default=False)
    confidence_score = models.FloatField(null=True, blank=True)
    garbage_type = models.CharField(max_length=50, choices=GARBAGE_TYPES, null=True, blank=True)
    severity_level = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='medium')
    
    # Bounding box coordinates (normalized 0-1)
    bbox_x = models.FloatField(null=True, blank=True)
    bbox_y = models.FloatField(null=True, blank=True)
    bbox_width = models.FloatField(null=True, blank=True)
    bbox_height = models.FloatField(null=True, blank=True)
    
    # Location data (copied from LocationData for this frame)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    location = models.PointField(geography=True, null=True, blank=True)
    
    # Frame image (extracted from video)
    frame_image = models.ImageField(upload_to='frames/%Y/%m/%d/', null=True, blank=True)
    annotated_image = models.ImageField(upload_to='annotated/%Y/%m/%d/', null=True, blank=True)
    
    # Full YOLO detection data (JSON)
    detection_data = models.JSONField(null=True, blank=True)
    
    class Meta:
        ordering = ['frame_number']
        unique_together = ['session', 'frame_number']
        indexes = [
            models.Index(fields=['session', 'garbage_detected']),
            models.Index(fields=['garbage_type']),
            models.Index(fields=['severity_level']),
        ]
    
    def save(self, *args, **kwargs):
        # Create Point object for spatial queries
        if self.latitude and self.longitude:
            self.location = Point(self.longitude, self.latitude)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Frame {self.frame_number} - Garbage: {self.garbage_detected}"

class GarbageLocation(models.Model):
    """Aggregated garbage locations for map display"""
    
    STATUS_CHOICES = [
        ('reported', 'Reported'),
        ('assigned', 'Assigned to Worker'),
        ('in_progress', 'Cleaning in Progress'),
        ('completed', 'Cleaned'),
        ('verified', 'Verified Clean'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    # Unique identifier
    location_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    
    # Geographic data
    latitude = models.FloatField()
    longitude = models.FloatField()
    location = models.PointField(geography=True)
    address = models.CharField(max_length=500, null=True, blank=True)
    
    # Garbage information
    garbage_type = models.CharField(max_length=50, choices=GarbageDetection.GARBAGE_TYPES)
    severity_level = models.CharField(max_length=20, choices=GarbageDetection.SEVERITY_LEVELS)
    priority = models.CharField(max_length=20, choices=PRIORITY_LEVELS, default='medium')
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='reported')
    
    # Related detections
    detections = models.ManyToManyField(GarbageDetection, related_name='garbage_locations')
    
    # Cleanup tracking
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='assigned_locations')
    assigned_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='verified_locations')
    
    # Images
    reference_image = models.ImageField(upload_to='garbage_locations/%Y/%m/%d/', null=True, blank=True)
    completion_image = models.ImageField(upload_to='completed/%Y/%m/%d/', null=True, blank=True)
    
    # Metadata
    detection_count = models.IntegerField(default=1)
    confidence_avg = models.FloatField(null=True, blank=True)
    
    # Timestamps
    first_detected = models.DateTimeField(auto_now_add=True)
    last_detected = models.DateTimeField(auto_now=True)
    
    # Notes
    description = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-first_detected']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['garbage_type']),
            models.Index(fields=['assigned_to']),
        ]
    
    def save(self, *args, **kwargs):
        # Create Point object
        if self.latitude and self.longitude:
            self.location = Point(self.longitude, self.latitude)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Garbage at ({self.latitude:.4f}, {self.longitude:.4f}) - {self.get_status_display()}"
    
    def get_status_color(self):
        """Return color for map markers"""
        colors = {
            'reported': 'red',
            'assigned': 'orange',
            'in_progress': 'yellow',
            'completed': 'blue',
            'verified': 'green',
        }
        return colors.get(self.status, 'gray')

class WorkerProfile(models.Model):
    """Extended profile for cleanup workers"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True)
    employee_id = models.CharField(max_length=50, unique=True)
    
    # Current location (for assignment optimization)
    current_latitude = models.FloatField(null=True, blank=True)
    current_longitude = models.FloatField(null=True, blank=True)
    current_location = models.PointField(geography=True, null=True, blank=True)
    location_updated = models.DateTimeField(null=True, blank=True)
    
    # Work status
    is_active = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True)
    
    # Statistics
    total_assignments = models.IntegerField(default=0)
    completed_cleanups = models.IntegerField(default=0)
    
    def __str__(self):
        return f"Worker: {self.user.get_full_name() or self.user.username}"
    
    def update_location(self, latitude, longitude):
        """Update worker's current location"""
        self.current_latitude = latitude
        self.current_longitude = longitude
        self.current_location = Point(longitude, latitude)
        self.location_updated = timezone.now()
        self.save()

class CleanupActivity(models.Model):
    """Track cleanup activities and progress"""
    
    ACTIVITY_TYPES = [
        ('assigned', 'Location Assigned'),
        ('started', 'Cleanup Started'),
        ('progress', 'Progress Update'),
        ('completed', 'Cleanup Completed'),
        ('verified', 'Cleanup Verified'),
        ('reopened', 'Location Reopened'),
    ]
    
    garbage_location = models.ForeignKey(GarbageLocation, on_delete=models.CASCADE, 
                                        related_name='activities')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    
    # Activity details
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='activities/%Y/%m/%d/', null=True, blank=True)
    
    # Location when activity occurred
    activity_latitude = models.FloatField(null=True, blank=True)
    activity_longitude = models.FloatField(null=True, blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'Cleanup Activities'
    
    def __str__(self):
        return f"{self.get_activity_type_display()} - {self.garbage_location.location_id}"