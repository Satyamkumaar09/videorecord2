package com.example.videolocationtracker.camera

import android.content.ContentValues
import android.content.Context
import android.net.Uri
import android.provider.MediaStore
import android.util.Log
import androidx.camera.core.CameraSelector
import androidx.camera.video.*
import androidx.camera.video.VideoCapture
import androidx.core.content.ContextCompat
import com.example.videolocationtracker.data.LocationData
import com.example.videolocationtracker.data.VideoLocationSession
import com.example.videolocationtracker.location.LocationManager
import com.example.videolocationtracker.network.NetworkManager
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import java.text.SimpleDateFormat
import java.util.*
import kotlin.collections.mutableListOf

class VideoRecordingManager(
    private val context: Context,
    private val locationManager: LocationManager
) {
    
    private val networkManager = NetworkManager(context)
    
    private val _isRecording = MutableStateFlow(false)
    val isRecording: StateFlow<Boolean> = _isRecording.asStateFlow()
    
    private val _recordingDuration = MutableStateFlow(0L)
    val recordingDuration: StateFlow<Long> = _recordingDuration.asStateFlow()
    
    private val _recordingStatus = MutableStateFlow("Ready")
    val recordingStatus: StateFlow<String> = _recordingStatus.asStateFlow()
    
    private var videoCapture: VideoCapture<Recorder>? = null
    private var recording: Recording? = null
    private var recordingJob: Job? = null
    
    // Location tracking variables
    private var currentFrameNumber = 0
    private var framesPerLocationUpdate = 30 // Default: update every 30 frames (1 second at 30fps)
    private val locationDataList = mutableListOf<LocationData>()
    private var sessionStartTime = 0L
    private var currentVideoFilename = ""
    private var sessionId = ""
    private var currentVideoFile: File? = null
    
    fun setupVideoCapture(): VideoCapture<Recorder> {
        val recorder = Recorder.Builder()
            .setQualitySelector(QualitySelector.from(Quality.HD))
            .build()
        
        videoCapture = VideoCapture.withOutput(recorder)
        return videoCapture!!
    }
    
    fun setLocationUpdateFrequency(framesPerUpdate: Int) {
        framesPerLocationUpdate = framesPerUpdate
    }
    
    fun startRecording() {
        val videoCapture = videoCapture ?: return
        
        // Generate unique filename and session ID
        sessionId = UUID.randomUUID().toString()
        val timestamp = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault()).format(Date())
        currentVideoFilename = "VID_${timestamp}.mp4"
        
        val contentValues = ContentValues().apply {
            put(MediaStore.MediaColumns.DISPLAY_NAME, currentVideoFilename)
            put(MediaStore.MediaColumns.MIME_TYPE, "video/mp4")
            put(MediaStore.Video.Media.RELATIVE_PATH, "Movies/VideoLocationTracker")
        }
        
        val mediaStoreOutputOptions = MediaStoreOutputOptions
            .Builder(context.contentResolver, MediaStore.Video.Media.EXTERNAL_CONTENT_URI)
            .setContentValues(contentValues)
            .build()
        
        recording = videoCapture.output
            .prepareRecording(context, mediaStoreOutputOptions)
            .apply {
                // Enable audio recording if permission is available
                if (hasAudioPermission()) {
                    withAudioEnabled()
                }
            }
            .start(ContextCompat.getMainExecutor(context)) { recordEvent ->
                when (recordEvent) {
                    is VideoRecordEvent.Start -> {
                        _isRecording.value = true
                        _recordingStatus.value = "Recording"
                        startLocationTracking()
                        startRecordingTimer()
                    }
                    is VideoRecordEvent.Finalize -> {
                        if (!recordEvent.hasError()) {
                            _recordingStatus.value = "Video saved successfully"
                            currentVideoFile = recordEvent.outputResults.outputUri?.let { uri ->
                                // Convert URI to File for upload
                                getFileFromUri(uri)
                            }
                            saveLocationDataAndUpload()
                        } else {
                            _recordingStatus.value = "Recording failed: ${recordEvent.error}"
                        }
                        _isRecording.value = false
                        stopLocationTracking()
                        stopRecordingTimer()
                    }
                }
            }
    }
    
    fun stopRecording() {
        recording?.stop()
        recording = null
    }
    
    private fun startLocationTracking() {
        sessionStartTime = System.currentTimeMillis()
        currentFrameNumber = 0
        locationDataList.clear()
        
        // Start location updates
        locationManager.startLocationUpdates()
    }
    
    private fun stopLocationTracking() {
        locationManager.stopLocationUpdates()
    }
    
    private fun startRecordingTimer() {
        recordingJob = CoroutineScope(Dispatchers.Main).launch {
            val startTime = System.currentTimeMillis()
            while (_isRecording.value) {
                val elapsed = System.currentTimeMillis() - startTime
                _recordingDuration.value = elapsed
                
                // Simulate frame counting (assuming 30 FPS)
                currentFrameNumber = ((elapsed / 1000.0) * 30).toInt()
                
                // Check if we need to capture location data
                if (currentFrameNumber % framesPerLocationUpdate == 0) {
                    captureLocationForCurrentFrame()
                }
                
                delay(33) // ~30 FPS update rate
            }
        }
    }
    
    private fun stopRecordingTimer() {
        recordingJob?.cancel()
        recordingJob = null
        _recordingDuration.value = 0L
    }
    
    private fun captureLocationForCurrentFrame() {
        locationManager.getCurrentLocationData(currentFrameNumber, framesPerLocationUpdate)?.let { locationData ->
            locationDataList.add(locationData)
        }
    }
    
    private fun saveLocationDataAndUpload() {
        if (locationDataList.isEmpty()) return
        
        val session = VideoLocationSession(
            sessionId = sessionId,
            videoFilename = currentVideoFilename,
            startTime = sessionStartTime,
            endTime = System.currentTimeMillis(),
            totalFrames = currentFrameNumber,
            fps = 30,
            locationUpdateInterval = framesPerLocationUpdate,
            locations = locationDataList.toList()
        )
        
        // Save to JSON file locally first
        val jsonFileManager = JsonFileManager(context)
        jsonFileManager.saveLocationSession(session)
        
        // Upload to Django backend
        uploadToServer(session)
    }
    
    private fun uploadToServer(session: VideoLocationSession) {
        CoroutineScope(Dispatchers.Main).launch {
            try {
                _recordingStatus.value = "Uploading data..."
                
                // Check if video file exists for upload
                val videoFile = currentVideoFile
                
                if (videoFile != null && videoFile.exists()) {
                    // Upload both location data and video
                    val result = networkManager.uploadCompleteSession(
                        session = session,
                        videoFile = videoFile,
                        onProgress = { progress ->
                            _recordingStatus.value = progress
                        }
                    )
                    
                    result.fold(
                        onSuccess = { (locationResponse, videoResponse) ->
                            if (videoResponse != null) {
                                _recordingStatus.value = "Upload completed successfully!"
                            } else {
                                _recordingStatus.value = "Location data uploaded, video upload failed"
                            }
                        },
                        onFailure = { error ->
                            _recordingStatus.value = "Upload failed: ${error.message}"
                            Log.e("VideoRecordingManager", "Upload failed", error)
                        }
                    )
                } else {
                    // Upload only location data
                    val result = networkManager.uploadLocationData(session)
                    
                    result.fold(
                        onSuccess = { response ->
                            _recordingStatus.value = "Location data uploaded successfully!"
                        },
                        onFailure = { error ->
                            _recordingStatus.value = "Upload failed: ${error.message}"
                            Log.e("VideoRecordingManager", "Location upload failed", error)
                        }
                    )
                }
                
            } catch (e: Exception) {
                _recordingStatus.value = "Upload error: ${e.message}"
                Log.e("VideoRecordingManager", "Upload error", e)
            }
        }
    }
    
    private fun getFileFromUri(uri: Uri): File? {
        return try {
            // For MediaStore URIs, we need to copy to a temporary file
            // This is a simplified approach - in production you might want more robust handling
            val inputStream = context.contentResolver.openInputStream(uri)
            val tempFile = File(context.cacheDir, currentVideoFilename)
            
            inputStream?.use { input ->
                tempFile.outputStream().use { output ->
                    input.copyTo(output)
                }
            }
            
            tempFile
        } catch (e: Exception) {
            Log.e("VideoRecordingManager", "Error converting URI to File", e)
            null
        }
    }
    
    private fun hasAudioPermission(): Boolean {
        return context.checkSelfPermission(android.Manifest.permission.RECORD_AUDIO) == 
                android.content.pm.PackageManager.PERMISSION_GRANTED
    }
    
    fun formatDuration(milliseconds: Long): String {
        val seconds = (milliseconds / 1000) % 60
        val minutes = (milliseconds / (1000 * 60)) % 60
        val hours = (milliseconds / (1000 * 60 * 60)) % 24
        
        return if (hours > 0) {
            String.format("%02d:%02d:%02d", hours, minutes, seconds)
        } else {
            String.format("%02d:%02d", minutes, seconds)
        }
    }
}