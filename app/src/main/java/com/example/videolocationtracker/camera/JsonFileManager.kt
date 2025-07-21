package com.example.videolocationtracker.camera

import android.content.Context
import android.os.Environment
import android.util.Log
import com.example.videolocationtracker.data.VideoLocationSession
import com.google.gson.Gson
import com.google.gson.GsonBuilder
import java.io.File
import java.io.FileWriter
import java.io.IOException
import java.text.SimpleDateFormat
import java.util.*

class JsonFileManager(private val context: Context) {
    
    private val gson: Gson = GsonBuilder()
        .setPrettyPrinting()
        .create()
    
    companion object {
        private const val TAG = "JsonFileManager"
        private const val FOLDER_NAME = "VideoLocationTracker"
        private const val JSON_EXTENSION = ".json"
    }
    
    fun saveLocationSession(session: VideoLocationSession) {
        try {
            val jsonString = gson.toJson(session)
            val file = createJsonFile(session.sessionId)
            
            FileWriter(file).use { writer ->
                writer.write(jsonString)
            }
            
            Log.d(TAG, "Location data saved to: ${file.absolutePath}")
            
        } catch (e: IOException) {
            Log.e(TAG, "Error saving location data", e)
        }
    }
    
    private fun createJsonFile(sessionId: String): File {
        // Create directory in external storage
        val documentsDir = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOCUMENTS)
        val appDir = File(documentsDir, FOLDER_NAME)
        
        if (!appDir.exists()) {
            appDir.mkdirs()
        }
        
        // Create filename with timestamp
        val timestamp = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault()).format(Date())
        val filename = "location_data_${timestamp}${JSON_EXTENSION}"
        
        return File(appDir, filename)
    }
    
    fun getAllLocationSessions(): List<VideoLocationSession> {
        val sessions = mutableListOf<VideoLocationSession>()
        
        try {
            val documentsDir = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOCUMENTS)
            val appDir = File(documentsDir, FOLDER_NAME)
            
            if (appDir.exists() && appDir.isDirectory) {
                appDir.listFiles { file -> file.name.endsWith(JSON_EXTENSION) }?.forEach { file ->
                    try {
                        val jsonString = file.readText()
                        val session = gson.fromJson(jsonString, VideoLocationSession::class.java)
                        sessions.add(session)
                    } catch (e: Exception) {
                        Log.e(TAG, "Error reading file: ${file.name}", e)
                    }
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error reading location sessions", e)
        }
        
        return sessions.sortedByDescending { it.startTime }
    }
    
    fun deleteLocationSession(sessionId: String): Boolean {
        try {
            val documentsDir = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOCUMENTS)
            val appDir = File(documentsDir, FOLDER_NAME)
            
            if (appDir.exists() && appDir.isDirectory) {
                appDir.listFiles { file -> file.name.endsWith(JSON_EXTENSION) }?.forEach { file ->
                    try {
                        val jsonString = file.readText()
                        val session = gson.fromJson(jsonString, VideoLocationSession::class.java)
                        if (session.sessionId == sessionId) {
                            return file.delete()
                        }
                    } catch (e: Exception) {
                        Log.e(TAG, "Error checking file: ${file.name}", e)
                    }
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error deleting location session", e)
        }
        
        return false
    }
}