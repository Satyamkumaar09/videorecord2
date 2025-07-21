from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json
import os
import uuid
from datetime import datetime
import shutil
from pathlib import Path

# Create FastAPI app
app = FastAPI(title="Video Location Tracker API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your Android app's origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data storage directory
STORAGE_DIR = Path("storage")
VIDEO_DIR = STORAGE_DIR / "videos"
JSON_DIR = STORAGE_DIR / "location_data"

# Create directories if they don't exist
VIDEO_DIR.mkdir(parents=True, exist_ok=True)
JSON_DIR.mkdir(parents=True, exist_ok=True)

# Pydantic models matching Android data structures
class LocationData(BaseModel):
    latitude: float
    longitude: float
    altitude: Optional[float] = None
    accuracy: Optional[float] = None
    timestamp: int
    frame_start: int
    frame_end: int
    address: Optional[str] = None

class VideoLocationSession(BaseModel):
    session_id: str
    video_filename: str
    start_time: int
    end_time: int
    total_frames: int
    fps: int
    location_update_interval: int
    locations: List[LocationData]

class UploadResponse(BaseModel):
    success: bool
    message: str
    session_id: Optional[str] = None
    file_url: Optional[str] = None

class SessionSummary(BaseModel):
    session_id: str
    video_filename: str
    start_time: int
    duration_seconds: int
    location_count: int
    upload_status: str

class DeleteResponse(BaseModel):
    success: bool
    message: str

# In-memory storage for session metadata (in production, use a database)
sessions_db = {}

@app.get("/")
async def root():
    return {"message": "Video Location Tracker API", "status": "running"}

@app.post("/api/v1/upload-location-data/", response_model=UploadResponse)
async def upload_location_data(session: VideoLocationSession):
    """
    Upload location data (JSON) from Android app
    """
    try:
        # Save JSON file
        json_filename = f"location_data_{session.session_id}.json"
        json_filepath = JSON_DIR / json_filename
        
        with open(json_filepath, 'w') as f:
            json.dump(session.dict(), f, indent=2)
        
        # Store session metadata
        sessions_db[session.session_id] = {
            "session_id": session.session_id,
            "video_filename": session.video_filename,
            "start_time": session.start_time,
            "end_time": session.end_time,
            "duration_seconds": (session.end_time - session.start_time) // 1000,
            "location_count": len(session.locations),
            "upload_status": "location_uploaded",
            "json_file": str(json_filepath),
            "video_file": None
        }
        
        return UploadResponse(
            success=True,
            message="Location data uploaded successfully",
            session_id=session.session_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading location data: {str(e)}")

@app.post("/api/v1/upload-video/", response_model=UploadResponse)
async def upload_video(
    session_id: str = Form(...),
    video: UploadFile = File(...)
):
    """
    Upload video file from Android app
    """
    try:
        # Validate file type
        if not video.content_type.startswith('video/'):
            raise HTTPException(status_code=400, detail="File must be a video")
        
        # Generate unique filename
        file_extension = video.filename.split('.')[-1] if '.' in video.filename else 'mp4'
        video_filename = f"video_{session_id}.{file_extension}"
        video_filepath = VIDEO_DIR / video_filename
        
        # Save video file
        with open(video_filepath, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)
        
        # Update session metadata
        if session_id in sessions_db:
            sessions_db[session_id]["video_file"] = str(video_filepath)
            sessions_db[session_id]["upload_status"] = "complete"
        else:
            # Create session if it doesn't exist
            sessions_db[session_id] = {
                "session_id": session_id,
                "video_filename": video.filename,
                "start_time": int(datetime.now().timestamp() * 1000),
                "end_time": int(datetime.now().timestamp() * 1000),
                "duration_seconds": 0,
                "location_count": 0,
                "upload_status": "video_only",
                "json_file": None,
                "video_file": str(video_filepath)
            }
        
        return UploadResponse(
            success=True,
            message="Video uploaded successfully",
            session_id=session_id,
            file_url=f"/api/v1/videos/{video_filename}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading video: {str(e)}")

@app.get("/api/v1/sessions/", response_model=List[SessionSummary])
async def get_all_sessions():
    """
    Get all uploaded sessions
    """
    try:
        sessions = []
        for session_data in sessions_db.values():
            sessions.append(SessionSummary(
                session_id=session_data["session_id"],
                video_filename=session_data["video_filename"],
                start_time=session_data["start_time"],
                duration_seconds=session_data["duration_seconds"],
                location_count=session_data["location_count"],
                upload_status=session_data["upload_status"]
            ))
        
        # Sort by start_time (newest first)
        sessions.sort(key=lambda x: x.start_time, reverse=True)
        return sessions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching sessions: {str(e)}")

@app.get("/api/v1/sessions/{session_id}/", response_model=VideoLocationSession)
async def get_session_details(session_id: str):
    """
    Get detailed location data for a specific session
    """
    try:
        if session_id not in sessions_db:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_data = sessions_db[session_id]
        json_file = session_data.get("json_file")
        
        if not json_file or not os.path.exists(json_file):
            raise HTTPException(status_code=404, detail="Location data not found")
        
        with open(json_file, 'r') as f:
            location_data = json.load(f)
        
        return VideoLocationSession(**location_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching session details: {str(e)}")

@app.delete("/api/v1/sessions/{session_id}/", response_model=DeleteResponse)
async def delete_session(session_id: str):
    """
    Delete a session and its associated files
    """
    try:
        if session_id not in sessions_db:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_data = sessions_db[session_id]
        
        # Delete JSON file
        json_file = session_data.get("json_file")
        if json_file and os.path.exists(json_file):
            os.remove(json_file)
        
        # Delete video file
        video_file = session_data.get("video_file")
        if video_file and os.path.exists(video_file):
            os.remove(video_file)
        
        # Remove from database
        del sessions_db[session_id]
        
        return DeleteResponse(
            success=True,
            message="Session deleted successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting session: {str(e)}")

@app.get("/api/v1/sessions/{session_id}/export/")
async def export_session_data(session_id: str, format: str = "json"):
    """
    Export session data in different formats (JSON, CSV, KML)
    """
    try:
        if session_id not in sessions_db:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_data = sessions_db[session_id]
        json_file = session_data.get("json_file")
        
        if not json_file or not os.path.exists(json_file):
            raise HTTPException(status_code=404, detail="Location data not found")
        
        with open(json_file, 'r') as f:
            location_data = json.load(f)
        
        if format.lower() == "json":
            return location_data
        elif format.lower() == "csv":
            # Convert to CSV format
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'frame_start', 'frame_end', 'latitude', 'longitude', 
                'altitude', 'accuracy', 'timestamp'
            ])
            
            # Write data
            for loc in location_data['locations']:
                writer.writerow([
                    loc['frame_start'], loc['frame_end'], loc['latitude'], 
                    loc['longitude'], loc.get('altitude', ''), 
                    loc.get('accuracy', ''), loc['timestamp']
                ])
            
            return {"csv_data": output.getvalue()}
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported format")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting data: {str(e)}")

@app.get("/api/v1/stats/")
async def get_statistics():
    """
    Get overall statistics
    """
    try:
        total_sessions = len(sessions_db)
        total_locations = sum(session["location_count"] for session in sessions_db.values())
        total_duration = sum(session["duration_seconds"] for session in sessions_db.values())
        
        return {
            "total_sessions": total_sessions,
            "total_locations": total_locations,
            "total_duration_seconds": total_duration,
            "average_duration_seconds": total_duration / total_sessions if total_sessions > 0 else 0,
            "average_locations_per_session": total_locations / total_sessions if total_sessions > 0 else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching statistics: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)