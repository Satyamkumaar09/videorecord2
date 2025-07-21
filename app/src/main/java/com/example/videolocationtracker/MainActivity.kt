package com.example.videolocationtracker

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.view.View
import android.widget.ArrayAdapter
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.camera.core.CameraSelector
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import com.example.videolocationtracker.camera.VideoRecordingManager
import com.example.videolocationtracker.databinding.ActivityMainBinding
import com.example.videolocationtracker.location.LocationManager
import kotlinx.coroutines.launch
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors

class MainActivity : AppCompatActivity() {
    
    private lateinit var binding: ActivityMainBinding
    private lateinit var locationManager: LocationManager
    private lateinit var videoRecordingManager: VideoRecordingManager
    private lateinit var cameraExecutor: ExecutorService
    
    private var cameraProvider: ProcessCameraProvider? = null
    private var preview: Preview? = null
    private var cameraSelector = CameraSelector.DEFAULT_BACK_CAMERA
    
    companion object {
        private val REQUIRED_PERMISSIONS = arrayOf(
            Manifest.permission.CAMERA,
            Manifest.permission.RECORD_AUDIO,
            Manifest.permission.ACCESS_FINE_LOCATION,
            Manifest.permission.ACCESS_COARSE_LOCATION,
            Manifest.permission.WRITE_EXTERNAL_STORAGE
        )
    }
    
    private val requestPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        val allGranted = permissions.values.all { it }
        if (allGranted) {
            setupCamera()
            binding.permissionOverlay.visibility = View.GONE
        } else {
            showPermissionDeniedMessage()
        }
    }
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        // Initialize managers
        locationManager = LocationManager(this)
        videoRecordingManager = VideoRecordingManager(this, locationManager)
        cameraExecutor = Executors.newSingleThreadExecutor()
        
        setupUI()
        checkPermissions()
    }
    
    private fun setupUI() {
        // Setup location frequency spinner
        val frequencies = arrayOf("10 frames", "15 frames", "30 frames", "60 frames", "90 frames")
        val adapter = ArrayAdapter(this, android.R.layout.simple_spinner_item, frequencies)
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
        binding.spinnerLocationFrequency.adapter = adapter
        binding.spinnerLocationFrequency.setSelection(2) // Default to 30 frames
        
        // Setup button listeners
        binding.btnStartStop.setOnClickListener {
            if (videoRecordingManager.isRecording.value) {
                stopRecording()
            } else {
                startRecording()
            }
        }
        
        binding.btnSwitchCamera.setOnClickListener {
            switchCamera()
        }
        
        binding.btnRequestPermissions.setOnClickListener {
            requestPermissions()
        }
        
        // Observe states
        observeStates()
    }
    
    private fun observeStates() {
        lifecycleScope.launch {
            locationManager.locationStatus.collect { status ->
                binding.locationStatus.text = status
            }
        }
        
        lifecycleScope.launch {
            videoRecordingManager.isRecording.collect { isRecording ->
                updateRecordingUI(isRecording)
            }
        }
        
        lifecycleScope.launch {
            videoRecordingManager.recordingDuration.collect { duration ->
                binding.recordingTimer.text = videoRecordingManager.formatDuration(duration)
            }
        }
        
        lifecycleScope.launch {
            videoRecordingManager.recordingStatus.collect { status ->
                binding.recordingStatus.text = status
            }
        }
    }
    
    private fun updateRecordingUI(isRecording: Boolean) {
        if (isRecording) {
            binding.btnStartStop.text = "Stop Recording"
            binding.btnStartStop.backgroundTintList = ContextCompat.getColorStateList(this, android.R.color.holo_red_dark)
            binding.recordingTimer.visibility = View.VISIBLE
            binding.btnSwitchCamera.isEnabled = false
            binding.spinnerLocationFrequency.isEnabled = false
        } else {
            binding.btnStartStop.text = "Start Recording"
            binding.btnStartStop.backgroundTintList = ContextCompat.getColorStateList(this, android.R.color.holo_green_dark)
            binding.recordingTimer.visibility = View.GONE
            binding.btnSwitchCamera.isEnabled = true
            binding.spinnerLocationFrequency.isEnabled = true
        }
    }
    
    private fun checkPermissions() {
        if (allPermissionsGranted()) {
            setupCamera()
            binding.permissionOverlay.visibility = View.GONE
        } else {
            binding.permissionOverlay.visibility = View.VISIBLE
        }
    }
    
    private fun allPermissionsGranted() = REQUIRED_PERMISSIONS.all {
        ContextCompat.checkSelfPermission(baseContext, it) == PackageManager.PERMISSION_GRANTED
    }
    
    private fun requestPermissions() {
        requestPermissionLauncher.launch(REQUIRED_PERMISSIONS)
    }
    
    private fun setupCamera() {
        val cameraProviderFuture = ProcessCameraProvider.getInstance(this)
        cameraProviderFuture.addListener({
            cameraProvider = cameraProviderFuture.get()
            bindCameraUseCases()
        }, ContextCompat.getMainExecutor(this))
    }
    
    private fun bindCameraUseCases() {
        val cameraProvider = cameraProvider ?: return
        
        // Preview
        preview = Preview.Builder().build().also {
            it.setSurfaceProvider(binding.previewView.surfaceProvider)
        }
        
        // Video capture
        val videoCapture = videoRecordingManager.setupVideoCapture()
        
        try {
            // Unbind use cases before rebinding
            cameraProvider.unbindAll()
            
            // Bind use cases to camera
            cameraProvider.bindToLifecycle(
                this,
                cameraSelector,
                preview,
                videoCapture
            )
            
        } catch (exc: Exception) {
            Toast.makeText(this, "Failed to bind camera use cases", Toast.LENGTH_SHORT).show()
        }
    }
    
    private fun switchCamera() {
        cameraSelector = if (cameraSelector == CameraSelector.DEFAULT_BACK_CAMERA) {
            CameraSelector.DEFAULT_FRONT_CAMERA
        } else {
            CameraSelector.DEFAULT_BACK_CAMERA
        }
        bindCameraUseCases()
    }
    
    private fun startRecording() {
        // Set location update frequency based on spinner selection
        val selectedPosition = binding.spinnerLocationFrequency.selectedItemPosition
        val framesPerUpdate = when (selectedPosition) {
            0 -> 10
            1 -> 15
            2 -> 30
            3 -> 60
            4 -> 90
            else -> 30
        }
        
        videoRecordingManager.setLocationUpdateFrequency(framesPerUpdate)
        videoRecordingManager.startRecording()
    }
    
    private fun stopRecording() {
        videoRecordingManager.stopRecording()
    }
    
    private fun showPermissionDeniedMessage() {
        Toast.makeText(
            this,
            "Camera and location permissions are required for this app to work",
            Toast.LENGTH_LONG
        ).show()
    }
    
    override fun onDestroy() {
        super.onDestroy()
        cameraExecutor.shutdown()
        locationManager.stopLocationUpdates()
    }
}