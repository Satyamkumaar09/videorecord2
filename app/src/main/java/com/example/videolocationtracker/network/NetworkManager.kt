package com.example.videolocationtracker.network

import android.content.Context
import android.net.Uri
import android.util.Log
import com.example.videolocationtracker.data.VideoLocationSession
import com.google.gson.GsonBuilder
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.io.File
import java.util.concurrent.TimeUnit

class NetworkManager(private val context: Context) {
    
    companion object {
        private const val TAG = "NetworkManager"
        // Replace with your Django server URL
        private const val BASE_URL = "http://192.168.1.XXX:8000/" // Change XXX to your computer's IP
        private const val TIMEOUT_SECONDS = 60L
    }
    
    private val gson = GsonBuilder()
        .setLenient()
        .create()
    
    private val okHttpClient = OkHttpClient.Builder()
        .connectTimeout(TIMEOUT_SECONDS, TimeUnit.SECONDS)
        .readTimeout(TIMEOUT_SECONDS, TimeUnit.SECONDS)
        .writeTimeout(TIMEOUT_SECONDS, TimeUnit.SECONDS)
        .addInterceptor { chain ->
            val request = chain.request().newBuilder()
                .addHeader("Content-Type", "application/json")
                .addHeader("Accept", "application/json")
                .build()
            chain.proceed(request)
        }
        .build()
    
    private val retrofit = Retrofit.Builder()
        .baseUrl(BASE_URL)
        .client(okHttpClient)
        .addConverterFactory(GsonConverterFactory.create(gson))
        .build()
    
    private val apiService = retrofit.create(ApiService::class.java)
    
    /**
     * Upload location data (JSON) to Django backend
     */
    suspend fun uploadLocationData(session: VideoLocationSession): Result<UploadResponse> {
        return withContext(Dispatchers.IO) {
            try {
                Log.d(TAG, "Uploading location data for session: ${session.sessionId}")
                
                val response = apiService.uploadLocationData(session)
                
                if (response.isSuccessful) {
                    val uploadResponse = response.body()
                    if (uploadResponse?.success == true) {
                        Log.d(TAG, "Location data uploaded successfully")
                        Result.success(uploadResponse)
                    } else {
                        Log.e(TAG, "Upload failed: ${uploadResponse?.message}")
                        Result.failure(Exception(uploadResponse?.message ?: "Upload failed"))
                    }
                } else {
                    Log.e(TAG, "HTTP Error: ${response.code()} - ${response.message()}")
                    Result.failure(Exception("HTTP ${response.code()}: ${response.message()}"))
                }
                
            } catch (e: Exception) {
                Log.e(TAG, "Network error uploading location data", e)
                Result.failure(e)
            }
        }
    }
    
    /**
     * Upload video file to Django backend
     */
    suspend fun uploadVideo(sessionId: String, videoFile: File): Result<UploadResponse> {
        return withContext(Dispatchers.IO) {
            try {
                Log.d(TAG, "Uploading video file: ${videoFile.name}")
                
                if (!videoFile.exists()) {
                    return@withContext Result.failure(Exception("Video file does not exist"))
                }
                
                // Create request body for session ID
                val sessionIdBody = sessionId.toRequestBody("text/plain".toMediaTypeOrNull())
                
                // Create request body for video file
                val videoRequestBody = videoFile.asRequestBody("video/mp4".toMediaTypeOrNull())
                val videoPart = MultipartBody.Part.createFormData(
                    "video", 
                    videoFile.name, 
                    videoRequestBody
                )
                
                val response = apiService.uploadVideo(sessionIdBody, videoPart)
                
                if (response.isSuccessful) {
                    val uploadResponse = response.body()
                    if (uploadResponse?.success == true) {
                        Log.d(TAG, "Video uploaded successfully")
                        Result.success(uploadResponse)
                    } else {
                        Log.e(TAG, "Video upload failed: ${uploadResponse?.message}")
                        Result.failure(Exception(uploadResponse?.message ?: "Video upload failed"))
                    }
                } else {
                    Log.e(TAG, "HTTP Error uploading video: ${response.code()} - ${response.message()}")
                    Result.failure(Exception("HTTP ${response.code()}: ${response.message()}"))
                }
                
            } catch (e: Exception) {
                Log.e(TAG, "Network error uploading video", e)
                Result.failure(e)
            }
        }
    }
    
    /**
     * Upload both location data and video file
     */
    suspend fun uploadCompleteSession(
        session: VideoLocationSession, 
        videoFile: File,
        onProgress: (String) -> Unit = {}
    ): Result<Pair<UploadResponse, UploadResponse?>> {
        return withContext(Dispatchers.IO) {
            try {
                // Step 1: Upload location data first
                onProgress("Uploading location data...")
                val locationResult = uploadLocationData(session)
                
                if (locationResult.isFailure) {
                    return@withContext Result.failure(
                        locationResult.exceptionOrNull() ?: Exception("Location data upload failed")
                    )
                }
                
                // Step 2: Upload video file
                onProgress("Uploading video file...")
                val videoResult = uploadVideo(session.sessionId, videoFile)
                
                if (videoResult.isFailure) {
                    Log.w(TAG, "Video upload failed, but location data was uploaded successfully")
                    return@withContext Result.success(
                        Pair(locationResult.getOrThrow(), null)
                    )
                }
                
                onProgress("Upload completed successfully!")
                Result.success(Pair(locationResult.getOrThrow(), videoResult.getOrThrow()))
                
            } catch (e: Exception) {
                Log.e(TAG, "Error in complete session upload", e)
                Result.failure(e)
            }
        }
    }
    
    /**
     * Get all sessions from server
     */
    suspend fun getAllSessions(): Result<List<SessionSummary>> {
        return withContext(Dispatchers.IO) {
            try {
                val response = apiService.getAllSessions()
                if (response.isSuccessful) {
                    Result.success(response.body() ?: emptyList())
                } else {
                    Result.failure(Exception("HTTP ${response.code()}: ${response.message()}"))
                }
            } catch (e: Exception) {
                Log.e(TAG, "Error fetching sessions", e)
                Result.failure(e)
            }
        }
    }
    
    /**
     * Check if server is reachable
     */
    suspend fun checkServerConnection(): Boolean {
        return withContext(Dispatchers.IO) {
            try {
                val response = apiService.getAllSessions()
                response.isSuccessful
            } catch (e: Exception) {
                Log.e(TAG, "Server connection check failed", e)
                false
            }
        }
    }
    
    /**
     * Update base URL for different server configurations
     */
    fun updateServerUrl(newBaseUrl: String): NetworkManager {
        return NetworkManager(context).apply {
            // This would require rebuilding the retrofit instance
            // For simplicity, recommend restarting app with new URL
        }
    }
}