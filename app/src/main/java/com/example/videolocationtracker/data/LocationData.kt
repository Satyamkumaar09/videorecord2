package com.example.videolocationtracker.data

import com.google.gson.annotations.SerializedName

/**
 * Data class representing location information for a specific frame or time period
 */
data class LocationData(
    @SerializedName("latitude")
    val latitude: Double,
    
    @SerializedName("longitude")
    val longitude: Double,
    
    @SerializedName("altitude")
    val altitude: Double? = null,
    
    @SerializedName("accuracy")
    val accuracy: Float? = null,
    
    @SerializedName("timestamp")
    val timestamp: Long,
    
    @SerializedName("frame_start")
    val frameStart: Int,
    
    @SerializedName("frame_end")
    val frameEnd: Int,
    
    @SerializedName("address")
    val address: String? = null
)

/**
 * Container for all location data during a video recording session
 */
data class VideoLocationSession(
    @SerializedName("session_id")
    val sessionId: String,
    
    @SerializedName("video_filename")
    val videoFilename: String,
    
    @SerializedName("start_time")
    val startTime: Long,
    
    @SerializedName("end_time")
    val endTime: Long,
    
    @SerializedName("total_frames")
    val totalFrames: Int,
    
    @SerializedName("fps")
    val fps: Int,
    
    @SerializedName("location_update_interval")
    val locationUpdateInterval: Int, // frames per location update
    
    @SerializedName("locations")
    val locations: List<LocationData>
)

/**
 * Configuration for location tracking
 */
data class LocationConfig(
    val framesPerUpdate: Int = 30, // Update location every 30 frames (1 second at 30fps)
    val minLocationAccuracy: Float = 50f, // Minimum accuracy in meters
    val locationTimeout: Long = 10000L // 10 seconds timeout for location updates
)