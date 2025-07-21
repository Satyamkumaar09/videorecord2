# 🚀 Complete Setup Guide: Video Location Tracker

This guide will help you set up both the Android app and Django FastAPI backend to send location data from your Android device to your server.

## 📱 **Part 1: Android App Setup**

### **Step 1: Create Android Project**
1. **Open Android Studio**
2. **Create New Project**:
   - Choose "Empty Activity"
   - Name: "Video Location Tracker"
   - Package: `com.example.videolocationtracker`
   - Language: **Kotlin**
   - Minimum SDK: **API 24**

### **Step 2: Add Required Files**
Copy these files to your Android project:

#### **Essential Files to Copy:**
```
📁 app/
├── build.gradle                     ← Replace with provided version
├── src/main/
│   ├── AndroidManifest.xml          ← Replace with provided version
│   ├── java/com/example/videolocationtracker/
│   │   ├── MainActivity.kt          ← Replace with provided version
│   │   ├── data/
│   │   │   └── LocationData.kt      ← Create new file
│   │   ├── location/
│   │   │   └── LocationManager.kt   ← Create new file
│   │   ├── camera/
│   │   │   ├── VideoRecordingManager.kt  ← Create new file
│   │   │   └── JsonFileManager.kt   ← Create new file
│   │   └── network/
│   │       ├── ApiService.kt        ← Create new file
│   │       └── NetworkManager.kt    ← Create new file
│   └── res/
│       ├── layout/
│       │   └── activity_main.xml    ← Replace with provided version
│       └── values/
│           ├── strings.xml          ← Replace with provided version
│           └── themes.xml           ← Replace with provided version
```

### **Step 3: Configure Server IP**
1. **Open `NetworkManager.kt`**
2. **Find this line:**
   ```kotlin
   private const val BASE_URL = "http://192.168.1.100:8000/"
   ```
3. **Replace with your computer's IP address:**
   ```kotlin
   private const val BASE_URL = "http://YOUR_COMPUTER_IP:8000/"
   ```

#### **How to Find Your Computer's IP:**
- **Windows**: `ipconfig` in Command Prompt
- **Mac/Linux**: `ifconfig` in Terminal
- **Example**: `http://192.168.1.105:8000/`

### **Step 4: Build and Install**
1. **Sync Project** (Android Studio will download dependencies)
2. **Connect Android device** (USB debugging enabled)
3. **Build and Run** the app

---

## 🖥️ **Part 2: Django FastAPI Backend Setup**

### **Step 1: Create Backend Directory**
```bash
mkdir video_location_backend
cd video_location_backend
```

### **Step 2: Create Required Files**
Create these files in your backend directory:

#### **File 1: `main.py`**
Copy the provided Django FastAPI code

#### **File 2: `requirements.txt`**
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
pydantic==2.5.0
python-json-logger==2.0.7
```

#### **File 3: `run_server.py`**
Copy the provided server runner script

### **Step 3: Install and Run Backend**
```bash
# Install Python dependencies
pip install -r requirements.txt

# Run the server
python run_server.py
```

**OR run manually:**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### **Step 4: Verify Backend is Running**
1. **Open browser**: `http://localhost:8000`
2. **API Documentation**: `http://localhost:8000/docs`
3. **Should see**: "Video Location Tracker API" message

---

## 🔗 **Part 3: Testing the Connection**

### **Step 1: Test Server Connection**
1. **Open Android app**
2. **Grant all permissions** (Camera, Location, Storage)
3. **Check server status** at bottom of screen:
   - ✅ **"Connected"** (Green) = Working
   - ❌ **"Not Connected"** (Red) = Check IP/Server

### **Step 2: Test Video Recording with Upload**
1. **Start recording** a short 10-second video
2. **Move around** to get different GPS locations
3. **Stop recording**
4. **Watch status messages**:
   - "Video saved successfully"
   - "Uploading data..."
   - "Upload completed successfully!"

### **Step 3: Verify Data on Server**
1. **Check API**: `http://YOUR_IP:8000/api/v1/sessions/`
2. **Check files**:
   ```
   backend_directory/
   └── storage/
       ├── videos/          ← Video files
       └── location_data/   ← JSON files
   ```

---

## 📊 **Part 4: Understanding the Data Flow**

### **What Happens When You Record:**

1. **Android App**:
   - Records video at 30 FPS
   - Captures GPS location every X frames (configurable)
   - Saves video to device storage
   - Creates JSON with location data

2. **Upload Process**:
   - Sends JSON location data to Django backend
   - Sends video file to Django backend
   - Server stores both files

3. **Server Storage**:
   ```json
   {
     "session_id": "abc-123-def",
     "video_filename": "VID_20241214_143022.mp4",
     "total_frames": 900,
     "fps": 30,
     "location_update_interval": 30,
     "locations": [
       {
         "latitude": 37.7749,
         "longitude": -122.4194,
         "accuracy": 4.2,
         "frame_start": 0,
         "frame_end": 29
       }
     ]
   }
   ```

---

## ⚙️ **Part 5: Configuration Options**

### **Location Update Frequency**
Configure how often GPS location is captured:

| Setting | Update Interval | Use Case |
|---------|----------------|----------|
| **10 frames** | ~0.33 seconds | High precision tracking |
| **30 frames** | ~1 second | **Default - Recommended** |
| **60 frames** | ~2 seconds | Battery saving |
| **90 frames** | ~3 seconds | Minimal tracking |

### **Server Configuration**
In `NetworkManager.kt`, you can modify:
- **BASE_URL**: Your server address
- **TIMEOUT_SECONDS**: Network timeout (default: 60s)

---

## 🐛 **Part 6: Troubleshooting**

### **Common Issues:**

#### **"Not Connected" Server Status**
- ✅ Check server is running: `http://localhost:8000`
- ✅ Check IP address in `NetworkManager.kt`
- ✅ Check firewall settings
- ✅ Ensure both devices on same WiFi network

#### **Upload Failed**
- ✅ Check internet connection
- ✅ Check server logs for errors
- ✅ Verify file permissions on server

#### **No Location Data**
- ✅ Test outdoors (better GPS signal)
- ✅ Check location permissions granted
- ✅ Wait for "Location: Good" status

#### **Video Not Recording**
- ✅ Check camera permission
- ✅ Check storage space (need 1GB+ for long videos)
- ✅ Test on real device (not emulator)

---

## 📈 **Part 7: API Endpoints**

Your Django backend provides these endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/upload-location-data/` | POST | Upload JSON location data |
| `/api/v1/upload-video/` | POST | Upload video file |
| `/api/v1/sessions/` | GET | List all sessions |
| `/api/v1/sessions/{id}/` | GET | Get session details |
| `/api/v1/sessions/{id}/export/` | GET | Export data (JSON/CSV) |
| `/api/v1/stats/` | GET | Get statistics |

---

## 🎯 **Part 8: Production Considerations**

### **For Production Use:**
1. **Database**: Replace in-memory storage with PostgreSQL/MySQL
2. **Authentication**: Add API keys or OAuth
3. **File Storage**: Use cloud storage (AWS S3, Google Cloud)
4. **HTTPS**: Enable SSL certificates
5. **Error Handling**: Add comprehensive logging
6. **Backup**: Implement data backup strategies

### **Security Notes:**
- Change default server URL in production
- Add authentication for API endpoints
- Validate file uploads (size, type)
- Implement rate limiting

---

## ✅ **Success Checklist**

- [ ] Android Studio project created and files copied
- [ ] Server IP configured in `NetworkManager.kt`
- [ ] Django backend running on port 8000
- [ ] Android app shows "Connected" server status
- [ ] Test recording shows upload success
- [ ] Files appear in server storage directory
- [ ] API endpoints accessible at `http://YOUR_IP:8000/docs`

**🎉 Congratulations! Your video location tracking system is now ready!**

---

## 📞 **Support**

If you encounter issues:
1. Check Android Studio Logcat for error messages
2. Check server console for error logs
3. Verify network connectivity between devices
4. Test with shorter videos first (10-30 seconds)

The system is designed to handle 1-hour recordings with configurable location accuracy to balance battery life and precision!