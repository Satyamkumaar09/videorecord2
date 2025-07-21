# 🏙️ Smart City Garbage Detection System

A complete AI-powered waste management platform that combines mobile video recording with GPS tracking, YOLO-based garbage detection, and intelligent dashboard management.

## 🎯 **System Overview**

```
📱 Android App (Citizens)
    ↓ Records video + GPS location
    ↓ Uploads to Django backend
🖥️ Django Backend + YOLO AI
    ↓ Processes video frames
    ↓ Detects garbage with location
    ↓ Creates cleanup tasks
📊 Admin Dashboard (City Management)
    ↓ Views garbage locations on map
    ↓ Assigns cleanup tasks to workers
    ↓ Tracks cleanup progress
👷 Worker Interface
    ↓ Receives assignments
    ↓ Updates cleanup status
    ↓ Marks locations as clean
```

## 🚀 **Quick Start**

### **1. Backend Setup**
```bash
# Clone/create project directory
mkdir smart_city_garbage
cd smart_city_garbage

# Copy all Django files (models.py, views.py, etc.)
# Install dependencies
pip install -r requirements.txt

# Setup and run
python setup_and_run.py
```

### **2. Android App Setup**
```kotlin
// In NetworkManager.kt, update your server IP:
private const val BASE_URL = "http://192.168.1.100:8000/"  // Your actual IP
```

### **3. Access Dashboards**
- **Admin Dashboard**: `http://localhost:8000/admin/`
- **User Dashboard**: `http://localhost:8000/dashboard/`
- **Map View**: `http://localhost:8000/map/`
- **API Docs**: `http://localhost:8000/api/docs/`

## 📱 **Android App Features**

### **Core Functionality**
- ✅ **HD Video Recording** with CameraX
- ✅ **Real-time GPS Tracking** (configurable intervals)
- ✅ **Automatic Upload** to Django backend
- ✅ **Server Connection Status** monitoring
- ✅ **Battery Optimization** for long recordings

### **Location Tracking Options**
| Setting | Update Interval | Use Case | Battery Impact |
|---------|----------------|----------|----------------|
| **10 frames** | ~0.33 seconds | High precision | High |
| **30 frames** | ~1 second | **Recommended** | Medium |
| **60 frames** | ~2 seconds | Battery saving | Low |

### **Data Format Sent to Backend**
```json
{
  "session_id": "unique-uuid",
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
      "accuracy": 4.2,
      "timestamp": 1702565422000,
      "frame_start": 0,
      "frame_end": 29
    }
  ]
}
```

## 🤖 **YOLO AI Processing**

### **Garbage Detection Capabilities**
- **Plastic Bottles** 🍶
- **Plastic Bags** 🛍️
- **Food Waste** 🍎
- **Paper** 📄
- **Metal Cans** 🥫
- **Glass** 🍾
- **Cigarette Butts** 🚬
- **Other Garbage** 🗑️

### **Severity Classification**
- **Critical**: High-impact items (plastic bags, food waste)
- **High**: Significant items (bottles, cans, glass)
- **Medium**: Moderate impact items
- **Low**: Minor items

### **Location Aggregation**
- Groups detections within **50 meters**
- Calculates **average coordinates**
- Determines **predominant garbage type**
- Assigns **priority levels** (Low → Urgent)

## 📊 **Dashboard System**

### **🔧 Admin Dashboard Features**

#### **Map View**
- 🗺️ **Interactive map** with garbage locations
- 📍 **Color-coded markers** by status:
  - 🔴 **Red**: Reported (new)
  - 🟠 **Orange**: Assigned to worker
  - 🟡 **Yellow**: Cleaning in progress
  - 🔵 **Blue**: Completed
  - 🟢 **Green**: Verified clean

#### **Task Management**
- 📋 **Assign locations** to cleanup workers
- 👷 **Track worker progress** in real-time
- 📈 **Priority-based** task scheduling
- 📊 **Performance analytics**

#### **Verification System**
- ✅ **Mark locations as clean** (admin only)
- 📸 **Before/after photo** comparison
- 🔄 **Reopen locations** if needed
- 📝 **Add admin notes**

### **👥 User Dashboard Features**

#### **View-Only Access**
- 🗺️ **View garbage locations** on map
- 📊 **See detection statistics**
- 📱 **Browse uploaded videos**
- ❌ **Cannot mark as clean** (admin privilege)

#### **Detection Gallery**
- 🖼️ **Frame-by-frame** garbage detection results
- 📍 **GPS coordinates** for each detection
- 🎯 **Confidence scores** and garbage types
- 📊 **Detection summary** statistics

## 🏗️ **System Architecture**

### **Backend Components**

#### **Django Apps**
```
smart_city_garbage/
├── garbage_detection/     # Core models and YOLO processing
├── dashboard/            # Web dashboards (admin & user)
├── api/                 # REST API for Android app
└── smart_city/          # Main Django project
```

#### **Database Models**
- **VideoSession**: Video metadata and processing status
- **LocationData**: GPS coordinates for frame ranges
- **GarbageDetection**: Individual frame detection results
- **GarbageLocation**: Aggregated cleanup locations
- **WorkerProfile**: Cleanup worker information
- **CleanupActivity**: Activity tracking and progress

#### **API Endpoints**
```
POST /api/v1/upload-location-data/    # Android location upload
POST /api/v1/upload-video/            # Android video upload
GET  /api/v1/sessions/                # List all sessions
GET  /api/v1/sessions/{id}/           # Session details
POST /api/v1/sessions/{id}/process/   # Trigger processing
GET  /api/v1/health/                  # Health check
```

### **Processing Pipeline**
1. **Video Upload** → Django receives video + GPS data
2. **YOLO Processing** → AI detects garbage in frames
3. **Location Mapping** → Links detections to GPS coordinates
4. **Aggregation** → Groups nearby detections
5. **Task Creation** → Creates cleanup tasks
6. **Assignment** → Assigns tasks to workers
7. **Tracking** → Monitors cleanup progress
8. **Verification** → Admin verifies completion

## 🛠️ **Installation Guide**

### **Prerequisites**
- Python 3.8+
- Django 4.2+
- Redis (for background processing)
- Android Studio (for mobile app)
- YOLO model file (optional)

### **Backend Installation**

#### **1. System Dependencies**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip redis-server spatialite-bin

# macOS
brew install python redis spatialite-tools

# Windows
# Install Python from python.org
# Install Redis from https://redis.io/download
```

#### **2. Python Environment**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install requirements
pip install -r requirements.txt
```

#### **3. Django Setup**
```bash
# Run setup script
python setup_and_run.py

# OR manual setup:
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic
```

#### **4. Start Services**
```bash
# Terminal 1: Django server
python manage.py runserver 0.0.0.0:8000

# Terminal 2: Background processing
celery -A smart_city worker --loglevel=info

# Terminal 3: Redis (if not running as service)
redis-server
```

### **Android App Installation**

#### **1. Android Studio Setup**
- Create new project: "Video Location Tracker"
- Package: `com.example.videolocationtracker`
- Language: Kotlin
- Min SDK: API 24

#### **2. Copy Files**
Copy all Android files to appropriate directories:
```
app/
├── build.gradle                    # Dependencies
├── src/main/
│   ├── AndroidManifest.xml         # Permissions
│   ├── java/com/example/videolocationtracker/
│   │   ├── MainActivity.kt         # Main app
│   │   ├── data/LocationData.kt    # Data models
│   │   ├── location/LocationManager.kt  # GPS handling
│   │   ├── camera/VideoRecordingManager.kt  # Video recording
│   │   └── network/NetworkManager.kt  # Server communication
│   └── res/layout/activity_main.xml  # UI layout
```

#### **3. Configure Server Connection**
```kotlin
// In NetworkManager.kt
private const val BASE_URL = "http://YOUR_SERVER_IP:8000/"
```

#### **4. Build and Install**
- Sync project in Android Studio
- Connect Android device (USB debugging enabled)
- Build and run application

## 📋 **User Workflows**

### **👤 Citizen Workflow**
1. **Open app** → Grant camera/location permissions
2. **Select location frequency** (10-90 frames)
3. **Start recording** → Walk around area
4. **Stop recording** → Video uploads automatically
5. **View status** → "Upload completed successfully!"

### **🔧 Admin Workflow**
1. **Access admin dashboard** → `http://server:8000/admin/`
2. **View map** → See all reported garbage locations
3. **Review detections** → Check AI detection results
4. **Assign tasks** → Assign locations to workers
5. **Monitor progress** → Track cleanup status
6. **Verify completion** → Mark as verified clean

### **👷 Worker Workflow**
1. **Receive assignment** → Get notification of assigned location
2. **Navigate to location** → Use GPS coordinates
3. **Start cleanup** → Update status to "in progress"
4. **Complete cleanup** → Take completion photo
5. **Mark complete** → Update status to "completed"
6. **Admin verification** → Admin marks as "verified"

## 🔧 **Configuration Options**

### **YOLO Model Configuration**
```python
# In settings.py
YOLO_MODEL_PATH = 'models/garbage_detection.pt'  # Your custom model
YOLO_CONFIDENCE_THRESHOLD = 0.5  # Detection confidence threshold
```

### **Location Processing**
```python
# Proximity grouping distance (meters)
LOCATION_GROUPING_DISTANCE = 50

# Priority calculation factors
PRIORITY_FACTORS = {
    'critical_types': ['plastic_bag', 'food_waste'],
    'high_impact_types': ['plastic_bottle', 'metal_can', 'glass'],
    'confidence_threshold': 0.8,
    'detection_count_threshold': 5
}
```

### **File Upload Limits**
```python
# Maximum file sizes
FILE_UPLOAD_MAX_MEMORY_SIZE = 500 * 1024 * 1024  # 500MB
VIDEO_MAX_DURATION = 3600  # 1 hour in seconds
```

## 📊 **Performance Optimization**

### **For Large Scale Deployment**

#### **Database Optimization**
- Use **PostgreSQL** with PostGIS for production
- Add **database indexes** on frequently queried fields
- Implement **database connection pooling**

#### **Video Processing**
- Use **Celery** for background processing
- Implement **video compression** before processing
- Add **progress tracking** for long videos

#### **API Performance**
- Add **API rate limiting**
- Implement **caching** for frequent queries
- Use **CDN** for static file delivery

#### **Scaling Considerations**
- **Horizontal scaling** with multiple Django instances
- **Load balancing** for high traffic
- **Separate media storage** (AWS S3, Google Cloud)

## 🔒 **Security Features**

### **Authentication & Authorization**
- **Django admin** authentication
- **Role-based access** (Admin, Worker, User)
- **API key authentication** (for production)

### **Data Protection**
- **CSRF protection** enabled
- **SQL injection** prevention
- **File upload validation**
- **GPS data encryption** (optional)

### **Privacy Considerations**
- **Location data anonymization** options
- **Video retention policies**
- **GDPR compliance** features
- **Data export/deletion** capabilities

## 📈 **Analytics & Reporting**

### **System Metrics**
- 📊 **Total sessions** processed
- 🗑️ **Garbage detection** statistics
- 📍 **Location coverage** analysis
- ⏱️ **Processing time** metrics

### **Cleanup Efficiency**
- 👷 **Worker performance** tracking
- ⏰ **Average cleanup time**
- ✅ **Completion rates**
- 🔄 **Reopen frequency**

### **Environmental Impact**
- 📉 **Garbage reduction** over time
- 🗺️ **Hotspot identification**
- 📈 **Trend analysis**
- 📋 **Compliance reporting**

## 🚀 **Future Enhancements**

### **Planned Features**
- 🤖 **Real-time processing** during recording
- 📱 **Mobile worker app** for field teams
- 🔔 **Push notifications** for urgent tasks
- 📊 **Advanced analytics** dashboard
- 🌍 **Multi-city deployment** support

### **AI Improvements**
- 🎯 **Better garbage classification**
- 📏 **Size estimation** algorithms
- 🔮 **Predictive modeling** for hotspots
- 🖼️ **Image quality enhancement**

### **Integration Options**
- 🗺️ **Google Maps** integration
- 📧 **Email notifications**
- 📱 **SMS alerts** for workers
- 📊 **BI tool** connectors

## 🆘 **Troubleshooting**

### **Common Issues**

#### **Android App**
- **"Not Connected"**: Check server IP and firewall
- **Upload Failed**: Verify internet connection and file size
- **No Location**: Test outdoors with clear GPS signal
- **Camera Error**: Check permissions and device compatibility

#### **Django Backend**
- **YOLO Processing Failed**: Check model file and dependencies
- **Database Errors**: Verify migrations and permissions
- **Celery Not Working**: Check Redis connection
- **Static Files Missing**: Run `collectstatic` command

#### **Performance Issues**
- **Slow Processing**: Optimize YOLO model or reduce video quality
- **High Memory Usage**: Implement video streaming processing
- **Database Slow**: Add indexes and optimize queries

### **Debug Commands**
```bash
# Check Django logs
tail -f logs/django.log

# Test API endpoints
curl http://localhost:8000/api/v1/health/

# Check Celery status
celery -A smart_city status

# Database shell
python manage.py shell
```

## 📞 **Support & Documentation**

### **Getting Help**
- 📖 **Django Documentation**: https://docs.djangoproject.com/
- 🤖 **YOLO Documentation**: https://docs.ultralytics.com/
- 📱 **Android CameraX**: https://developer.android.com/camerax
- 🗺️ **Leaflet Maps**: https://leafletjs.com/

### **System Requirements**
- **Server**: 4GB RAM, 2 CPU cores, 50GB storage
- **Android**: API 24+, Camera, GPS, 2GB RAM
- **Network**: Stable internet for video uploads

This comprehensive system provides a complete solution for smart city waste management, combining mobile technology, AI detection, and efficient workflow management! 🏙️🗑️🤖