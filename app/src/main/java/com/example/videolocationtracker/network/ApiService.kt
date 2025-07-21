package com.example.videolocationtracker.network

import com.example.videolocationtracker.data.VideoLocationSession
import retrofit2.Response
import retrofit2.http.*

/**
 * API interface for communicating with Django FastAPI backend
 */
interface ApiService {
    
    @POST("api/v1/upload-location-data/")
    suspend fun uploadLocationData(
        @Body locationSession: VideoLocationSession
    ): Response<UploadResponse>
    
    @Multipart
    @POST("api/v1/upload-video/")
    suspend fun uploadVideo(
        @Part("session_id") sessionId: okhttp3.RequestBody,
        @Part video: okhttp3.MultipartBody.Part
    ): Response<UploadResponse>
    
    @GET("api/v1/sessions/")
    suspend fun getAllSessions(): Response<List<SessionSummary>>
    
    @GET("api/v1/sessions/{session_id}/")
    suspend fun getSessionDetails(
        @Path("session_id") sessionId: String
    ): Response<VideoLocationSession>
    
    @DELETE("api/v1/sessions/{session_id}/")
    suspend fun deleteSession(
        @Path("session_id") sessionId: String
    ): Response<DeleteResponse>
}

/**
 * Response models for API calls
 */
data class UploadResponse(
    val success: Boolean,
    val message: String,
    val session_id: String? = null,
    val file_url: String? = null
)

data class SessionSummary(
    val session_id: String,
    val video_filename: String,
    val start_time: Long,
    val duration_seconds: Int,
    val location_count: Int,
    val upload_status: String
)

data class DeleteResponse(
    val success: Boolean,
    val message: String
)