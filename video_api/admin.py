from django.contrib import admin
from .models import VideoSession, VideoFrame, FrameMetadata


@admin.register(VideoSession)
class VideoSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'total_frames', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(VideoFrame)
class VideoFrameAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'frame_number', 'uploaded_at']
    list_filter = ['session', 'uploaded_at']
    search_fields = ['session__name']
    readonly_fields = ['uploaded_at']


@admin.register(FrameMetadata)
class FrameMetadataAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'uploaded_at']
    list_filter = ['uploaded_at']
    readonly_fields = ['uploaded_at']
