# Video Location Tracker Android App

An Android application built with Kotlin that records video while simultaneously tracking GPS location data and saving it in JSON format. The app allows configurable location update intervals to balance accuracy with performance.

## Features

- **Video Recording**: High-quality video recording using CameraX
- **GPS Location Tracking**: Real-time location tracking during video recording
- **Configurable Refresh Rate**: Choose location update frequency (10, 15, 30, 60, 90 frames)
- **JSON Data Export**: Automatic export of location data in structured JSON format
- **Permission Management**: Handles camera, location, and storage permissions
- **Front/Back Camera Support**: Switch between cameras during recording
- **Real-time Status**: Live location accuracy and recording status display

## Location Refresh Rate Recommendations

### Frame-based Location Updates

The app allows you to configure how often location data is captured relative to video frames:

| Setting | Frames per Update | At 30 FPS | Recommended Use Case |
|---------|------------------|-----------|---------------------|
| **10 frames** | Every 10 frames | ~0.33 seconds | High precision tracking (sports, detailed movement) |
| **15 frames** | Every 15 frames | ~0.5 seconds | Balanced precision (walking, cycling) |
| **30 frames** | Every 30 frames | ~1 second | **Default - Good balance** (general recording) |
| **60 frames** | Every 60 frames | ~2 seconds | Lower precision (stationary recording) |
| **90 frames** | Every 90 frames | ~3 seconds | Minimal tracking (battery saving) |

### Accuracy vs Performance Trade-offs

- **Higher Frequency (10-15 frames)**: 
  - ✅ More accurate location tracking
  - ✅ Better for moving subjects
  - ❌ Higher battery consumption
  - ❌ Larger JSON files

- **Lower Frequency (60-90 frames)**:
  - ✅ Better battery life
  - ✅ Smaller JSON files
  - ❌ Less precise location tracking
  - ❌ May miss quick movements

## Application Structure

```
app/
├── src/main/java/com/example/videolocationtracker/
│   ├── MainActivity.kt                 # Main activity with UI and camera setup
│   ├── data/
│   │   └── LocationData.kt            # Data classes for location information
│   ├── location/
│   │   └── LocationManager.kt         # GPS location tracking management
│   └── camera/
│       ├── VideoRecordingManager.kt   # Video recording with location integration
│       └── JsonFileManager.kt         # JSON file creation and management
├── src/main/res/
│   ├── layout/
│   │   └── activity_main.xml          # Main UI layout
│   ├── values/
│   │   ├── strings.xml               # String resources
│   │   └── themes.xml                # App themes
│   └── xml/
│       ├── backup_rules.xml          # Backup configuration
│       └── data_extraction_rules.xml # Data extraction rules
└── src/main/AndroidManifest.xml      # App permissions and configuration
```

## JSON Output Format

The app generates JSON files with the following structure:

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
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
      "frame_end": 29,
      "address": null
    }
  ]
}
```

### Field Descriptions

- **session_id**: Unique identifier for the recording session
- **video_filename**: Name of the recorded video file
- **start_time/end_time**: Recording timestamps in milliseconds
- **total_frames**: Total number of frames in the video
- **fps**: Frames per second (typically 30)
- **location_update_interval**: Number of frames between location updates
- **locations**: Array of location data points
  - **latitude/longitude**: GPS coordinates
  - **altitude**: Elevation in meters (if available)
  - **accuracy**: GPS accuracy in meters
  - **timestamp**: Location timestamp
  - **frame_start/frame_end**: Frame range for this location

## Permissions Required

- `CAMERA`: Video recording
- `RECORD_AUDIO`: Audio recording with video
- `ACCESS_FINE_LOCATION`: High-precision GPS
- `ACCESS_COARSE_LOCATION`: Network-based location
- `WRITE_EXTERNAL_STORAGE`: Save video and JSON files

## Dependencies

- **CameraX**: Modern camera API for Android
- **Google Play Services Location**: GPS and location services
- **Gson**: JSON serialization/deserialization
- **Kotlin Coroutines**: Asynchronous programming
- **Material Components**: Modern UI components

## Installation and Setup

1. **Clone the repository**
2. **Open in Android Studio**
3. **Build the project** (Gradle will download dependencies)
4. **Run on device** (Emulator won't have GPS for testing)

## Usage

1. **Grant Permissions**: Allow camera and location access
2. **Select Update Frequency**: Choose location update interval
3. **Start Recording**: Tap "Start Recording" button
4. **Record Video**: Camera preview shows live feed
5. **Stop Recording**: Tap "Stop Recording" when done
6. **Access Files**: 
   - Videos saved to `Movies/VideoLocationTracker/`
   - JSON files saved to `Documents/VideoLocationTracker/`

## Technical Considerations

### Location Accuracy
- **Excellent**: < 5 meters accuracy
- **Good**: 5-10 meters accuracy  
- **Fair**: 10-25 meters accuracy
- **Poor**: > 25 meters accuracy

### Battery Optimization
- Location updates consume battery
- Higher frequency = more battery usage
- Consider use case when selecting update interval

### Storage Requirements
- Video files: ~100MB per minute (HD quality)
- JSON files: ~1KB per location point
- Total storage scales with recording length and update frequency

## Error Handling

The app includes comprehensive error handling for:
- Permission denials
- GPS unavailability
- Camera access issues
- Storage write failures
- Network connectivity issues

## Future Enhancements

- **Address Geocoding**: Convert coordinates to addresses
- **Export Options**: CSV, KML export formats
- **Video Playback**: In-app video playback with location overlay
- **Cloud Sync**: Backup to cloud storage
- **Batch Processing**: Process multiple recordings together

This application provides a solid foundation for video recording with location tracking, suitable for various use cases from personal documentation to professional field work.