import cv2
import numpy as np
from ultralytics import YOLO
import logging
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone
from PIL import Image
import io
import os
from .models import VideoSession, GarbageDetection, LocationData, GarbageLocation
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import Distance

logger = logging.getLogger(__name__)

class GarbageYOLOProcessor:
    """YOLO processor for garbage detection in video frames"""
    
    def __init__(self, model_path=None):
        self.model_path = model_path or settings.YOLO_MODEL_PATH
        self.confidence_threshold = settings.YOLO_CONFIDENCE_THRESHOLD
        self.model = None
        self.load_model()
        
        # Garbage type mapping (adjust based on your YOLO model classes)
        self.class_mapping = {
            0: 'plastic_bottle',
            1: 'plastic_bag', 
            2: 'food_waste',
            3: 'paper',
            4: 'metal_can',
            5: 'glass',
            6: 'cigarette',
            7: 'other'
        }
    
    def load_model(self):
        """Load YOLO model"""
        try:
            if os.path.exists(self.model_path):
                self.model = YOLO(self.model_path)
                logger.info(f"YOLO model loaded from {self.model_path}")
            else:
                # Use default YOLOv8 model if custom model not found
                self.model = YOLO('yolov8n.pt')
                logger.warning(f"Custom model not found at {self.model_path}, using default YOLOv8")
        except Exception as e:
            logger.error(f"Error loading YOLO model: {e}")
            raise
    
    def process_video_session(self, session):
        """Process entire video session with YOLO"""
        try:
            logger.info(f"Starting YOLO processing for session {session.session_id}")
            
            # Update session status
            session.processing_status = 'processing'
            session.save()
            
            if not session.video_file:
                raise ValueError("No video file found for session")
            
            # Get location data for frame mapping
            location_map = self._build_location_map(session)
            
            # Process video frames
            results = self._process_video_frames(session, location_map)
            
            # Create aggregated garbage locations
            self._create_garbage_locations(session)
            
            # Update session with results
            session.processing_status = 'completed'
            session.yolo_processed = True
            session.total_garbage_frames = results['garbage_frames']
            session.garbage_detected = results['garbage_frames'] > 0
            session.processed_at = timezone.now()
            session.save()
            
            logger.info(f"YOLO processing completed for session {session.session_id}")
            return results
            
        except Exception as e:
            logger.error(f"Error processing video session {session.session_id}: {e}")
            session.processing_status = 'failed'
            session.save()
            raise
    
    def _build_location_map(self, session):
        """Build mapping of frame numbers to GPS coordinates"""
        location_map = {}
        locations = session.locations.all()
        
        for location in locations:
            for frame_num in range(location.frame_start, location.frame_end + 1):
                location_map[frame_num] = {
                    'latitude': location.latitude,
                    'longitude': location.longitude,
                    'accuracy': location.accuracy,
                    'address': location.address
                }
        
        return location_map
    
    def _process_video_frames(self, session, location_map):
        """Process video frames with YOLO detection"""
        video_path = session.video_file.path
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Cannot open video file: {video_path}")
        
        frame_count = 0
        garbage_frames = 0
        detections_created = []
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Run YOLO detection on frame
                results = self.model(frame, conf=self.confidence_threshold)
                
                # Process detection results
                frame_has_garbage = False
                for result in results:
                    if result.boxes is not None and len(result.boxes) > 0:
                        frame_has_garbage = True
                        detection = self._process_frame_detection(
                            session, frame_count, frame, result, location_map
                        )
                        if detection:
                            detections_created.append(detection)
                
                if frame_has_garbage:
                    garbage_frames += 1
                
                frame_count += 1
                
                # Log progress every 100 frames
                if frame_count % 100 == 0:
                    logger.info(f"Processed {frame_count} frames for session {session.session_id}")
        
        finally:
            cap.release()
        
        return {
            'total_frames': frame_count,
            'garbage_frames': garbage_frames,
            'detections': len(detections_created)
        }
    
    def _process_frame_detection(self, session, frame_number, frame, yolo_result, location_map):
        """Process YOLO detection for a single frame"""
        try:
            # Calculate frame timestamp
            frame_timestamp = session.start_time + (frame_number * (1000 // session.fps))
            
            # Get location data for this frame
            location_data = location_map.get(frame_number, {})
            
            # Process each detection in the frame
            best_detection = None
            highest_confidence = 0
            
            for box in yolo_result.boxes:
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                
                if confidence > highest_confidence:
                    highest_confidence = confidence
                    
                    # Get bounding box coordinates (normalized)
                    x1, y1, x2, y2 = box.xyxyn[0].tolist()
                    bbox_x = x1
                    bbox_y = y1
                    bbox_width = x2 - x1
                    bbox_height = y2 - y1
                    
                    # Map class ID to garbage type
                    garbage_type = self.class_mapping.get(class_id, 'other')
                    
                    # Determine severity based on confidence and garbage type
                    severity = self._determine_severity(confidence, garbage_type)
                    
                    best_detection = {
                        'confidence': confidence,
                        'garbage_type': garbage_type,
                        'severity': severity,
                        'bbox_x': bbox_x,
                        'bbox_y': bbox_y,
                        'bbox_width': bbox_width,
                        'bbox_height': bbox_height,
                    }
            
            if best_detection:
                # Create GarbageDetection object
                detection = GarbageDetection.objects.create(
                    session=session,
                    frame_number=frame_number,
                    timestamp=frame_timestamp,
                    garbage_detected=True,
                    confidence_score=best_detection['confidence'],
                    garbage_type=best_detection['garbage_type'],
                    severity_level=best_detection['severity'],
                    bbox_x=best_detection['bbox_x'],
                    bbox_y=best_detection['bbox_y'],
                    bbox_width=best_detection['bbox_width'],
                    bbox_height=best_detection['bbox_height'],
                    latitude=location_data.get('latitude'),
                    longitude=location_data.get('longitude'),
                    detection_data={
                        'yolo_result': yolo_result.tojson() if hasattr(yolo_result, 'tojson') else {},
                        'frame_number': frame_number,
                        'location_accuracy': location_data.get('accuracy')
                    }
                )
                
                # Save frame image and annotated image
                self._save_frame_images(detection, frame, yolo_result)
                
                return detection
            
        except Exception as e:
            logger.error(f"Error processing frame {frame_number}: {e}")
        
        return None
    
    def _determine_severity(self, confidence, garbage_type):
        """Determine severity level based on confidence and garbage type"""
        # High-impact garbage types
        critical_types = ['plastic_bag', 'food_waste']
        high_impact_types = ['plastic_bottle', 'metal_can', 'glass']
        
        if garbage_type in critical_types:
            return 'critical' if confidence > 0.8 else 'high'
        elif garbage_type in high_impact_types:
            return 'high' if confidence > 0.7 else 'medium'
        else:
            return 'medium' if confidence > 0.6 else 'low'
    
    def _save_frame_images(self, detection, frame, yolo_result):
        """Save original and annotated frame images"""
        try:
            # Save original frame
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_pil = Image.fromarray(frame_rgb)
            
            # Save to BytesIO
            frame_io = io.BytesIO()
            frame_pil.save(frame_io, format='JPEG', quality=85)
            frame_io.seek(0)
            
            # Save to model
            frame_filename = f"frame_{detection.session.session_id}_{detection.frame_number}.jpg"
            detection.frame_image.save(
                frame_filename,
                ContentFile(frame_io.read()),
                save=False
            )
            
            # Create annotated image
            annotated_frame = yolo_result.plot()
            annotated_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
            annotated_pil = Image.fromarray(annotated_rgb)
            
            # Save annotated image
            annotated_io = io.BytesIO()
            annotated_pil.save(annotated_io, format='JPEG', quality=85)
            annotated_io.seek(0)
            
            annotated_filename = f"annotated_{detection.session.session_id}_{detection.frame_number}.jpg"
            detection.annotated_image.save(
                annotated_filename,
                ContentFile(annotated_io.read()),
                save=False
            )
            
            detection.save()
            
        except Exception as e:
            logger.error(f"Error saving frame images: {e}")
    
    def _create_garbage_locations(self, session):
        """Create aggregated garbage locations from detections"""
        try:
            # Get all garbage detections with location data
            detections = session.detections.filter(
                garbage_detected=True,
                latitude__isnull=False,
                longitude__isnull=False
            )
            
            # Group detections by proximity (within 50 meters)
            location_groups = []
            processed_detections = set()
            
            for detection in detections:
                if detection.id in processed_detections:
                    continue
                
                detection_point = Point(detection.longitude, detection.latitude)
                nearby_detections = [detection]
                processed_detections.add(detection.id)
                
                # Find nearby detections
                for other_detection in detections:
                    if other_detection.id in processed_detections:
                        continue
                    
                    other_point = Point(other_detection.longitude, other_detection.latitude)
                    distance = detection_point.distance(other_point) * 111000  # Convert to meters
                    
                    if distance <= 50:  # Within 50 meters
                        nearby_detections.append(other_detection)
                        processed_detections.add(other_detection.id)
                
                location_groups.append(nearby_detections)
            
            # Create GarbageLocation objects
            for group in location_groups:
                if not group:
                    continue
                
                # Calculate average location
                avg_lat = sum(d.latitude for d in group) / len(group)
                avg_lng = sum(d.longitude for d in group) / len(group)
                avg_confidence = sum(d.confidence_score for d in group) / len(group)
                
                # Determine predominant garbage type and severity
                type_counts = {}
                severity_counts = {}
                
                for detection in group:
                    type_counts[detection.garbage_type] = type_counts.get(detection.garbage_type, 0) + 1
                    severity_counts[detection.severity_level] = severity_counts.get(detection.severity_level, 0) + 1
                
                predominant_type = max(type_counts, key=type_counts.get)
                predominant_severity = max(severity_counts, key=severity_counts.get)
                
                # Determine priority
                priority = self._calculate_priority(predominant_severity, len(group), avg_confidence)
                
                # Create or update garbage location
                garbage_location, created = GarbageLocation.objects.get_or_create(
                    latitude=round(avg_lat, 6),
                    longitude=round(avg_lng, 6),
                    garbage_type=predominant_type,
                    defaults={
                        'severity_level': predominant_severity,
                        'priority': priority,
                        'detection_count': len(group),
                        'confidence_avg': avg_confidence,
                        'description': f"Detected {len(group)} instances of {predominant_type}",
                        'reference_image': group[0].annotated_image if group[0].annotated_image else None
                    }
                )
                
                # Add detections to garbage location
                garbage_location.detections.add(*group)
                
                if not created:
                    # Update existing location
                    garbage_location.detection_count += len(group)
                    garbage_location.confidence_avg = (garbage_location.confidence_avg + avg_confidence) / 2
                    garbage_location.last_detected = timezone.now()
                    garbage_location.save()
                
                logger.info(f"Created/updated garbage location at ({avg_lat:.6f}, {avg_lng:.6f}) with {len(group)} detections")
        
        except Exception as e:
            logger.error(f"Error creating garbage locations: {e}")
    
    def _calculate_priority(self, severity, detection_count, confidence):
        """Calculate priority level for garbage location"""
        if severity == 'critical' or detection_count >= 10:
            return 'urgent'
        elif severity == 'high' or (detection_count >= 5 and confidence > 0.8):
            return 'high'
        elif severity == 'medium' or detection_count >= 3:
            return 'medium'
        else:
            return 'low'

# Celery task for async processing
from celery import shared_task

@shared_task
def process_video_async(session_id):
    """Async task to process video with YOLO"""
    try:
        session = VideoSession.objects.get(id=session_id)
        processor = GarbageYOLOProcessor()
        results = processor.process_video_session(session)
        
        logger.info(f"Async processing completed for session {session.session_id}")
        return {
            'session_id': str(session.session_id),
            'status': 'completed',
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Async processing failed for session {session_id}: {e}")
        try:
            session = VideoSession.objects.get(id=session_id)
            session.processing_status = 'failed'
            session.save()
        except:
            pass
        
        return {
            'session_id': session_id,
            'status': 'failed',
            'error': str(e)
        }