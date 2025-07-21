package com.example.videolocationtracker.location

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.location.Location
import android.os.Looper
import androidx.core.app.ActivityCompat
import com.google.android.gms.location.*
import com.google.android.gms.tasks.Task
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

class LocationManager(private val context: Context) {
    
    private val fusedLocationClient: FusedLocationProviderClient = 
        LocationServices.getFusedLocationProviderClient(context)
    
    private val _currentLocation = MutableStateFlow<Location?>(null)
    val currentLocation: StateFlow<Location?> = _currentLocation.asStateFlow()
    
    private val _locationStatus = MutableStateFlow("Location: Not Available")
    val locationStatus: StateFlow<String> = _locationStatus.asStateFlow()
    
    private var locationCallback: LocationCallback? = null
    private var isRequestingUpdates = false
    
    private val locationRequest = LocationRequest.Builder(
        Priority.PRIORITY_HIGH_ACCURACY,
        1000L // 1 second interval
    ).apply {
        setMinUpdateDistanceMeters(1f) // Update every 1 meter
        setGranularity(Granularity.GRANULARITY_PERMISSION_LEVEL)
        setWaitForAccurateLocation(false)
    }.build()
    
    fun hasLocationPermission(): Boolean {
        return ActivityCompat.checkSelfPermission(
            context,
            Manifest.permission.ACCESS_FINE_LOCATION
        ) == PackageManager.PERMISSION_GRANTED
    }
    
    fun startLocationUpdates() {
        if (!hasLocationPermission()) {
            _locationStatus.value = "Location: Permission Denied"
            return
        }
        
        if (isRequestingUpdates) return
        
        locationCallback = object : LocationCallback() {
            override fun onLocationResult(locationResult: LocationResult) {
                locationResult.lastLocation?.let { location ->
                    _currentLocation.value = location
                    updateLocationStatus(location)
                }
            }
            
            override fun onLocationAvailability(availability: LocationAvailability) {
                if (!availability.isLocationAvailable) {
                    _locationStatus.value = "Location: GPS Unavailable"
                }
            }
        }
        
        try {
            fusedLocationClient.requestLocationUpdates(
                locationRequest,
                locationCallback!!,
                Looper.getMainLooper()
            )
            isRequestingUpdates = true
            _locationStatus.value = "Location: Searching..."
        } catch (e: SecurityException) {
            _locationStatus.value = "Location: Permission Error"
        }
    }
    
    fun stopLocationUpdates() {
        locationCallback?.let { callback ->
            fusedLocationClient.removeLocationUpdates(callback)
        }
        isRequestingUpdates = false
        _locationStatus.value = "Location: Stopped"
    }
    
    fun getLastKnownLocation(): Task<Location?> {
        return if (hasLocationPermission()) {
            fusedLocationClient.lastLocation
        } else {
            throw SecurityException("Location permission not granted")
        }
    }
    
    private fun updateLocationStatus(location: Location) {
        val accuracy = location.accuracy
        val status = when {
            accuracy <= 5 -> "Location: Excellent (${accuracy.toInt()}m)"
            accuracy <= 10 -> "Location: Good (${accuracy.toInt()}m)"
            accuracy <= 25 -> "Location: Fair (${accuracy.toInt()}m)"
            else -> "Location: Poor (${accuracy.toInt()}m)"
        }
        _locationStatus.value = status
    }
    
    fun getCurrentLocationData(frameNumber: Int, framesPerUpdate: Int): com.example.videolocationtracker.data.LocationData? {
        val location = _currentLocation.value ?: return null
        
        val frameStart = (frameNumber / framesPerUpdate) * framesPerUpdate
        val frameEnd = frameStart + framesPerUpdate - 1
        
        return com.example.videolocationtracker.data.LocationData(
            latitude = location.latitude,
            longitude = location.longitude,
            altitude = if (location.hasAltitude()) location.altitude else null,
            accuracy = if (location.hasAccuracy()) location.accuracy else null,
            timestamp = location.time,
            frameStart = frameStart,
            frameEnd = frameEnd
        )
    }
}