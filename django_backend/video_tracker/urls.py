from django.urls import path
from . import views

urlpatterns = [
    # API endpoints for Android app
    path('api/v1/upload-location-data/', views.upload_location_data, name='upload_location_data'),
    path('api/v1/upload-video/', views.upload_video, name='upload_video'),
    path('api/v1/sessions/', views.get_sessions, name='get_sessions'),
    path('api/v1/sessions/<uuid:session_id>/', views.get_session_details, name='get_session_details'),
    path('api/v1/sessions/<uuid:session_id>/process/', views.process_video, name='process_video'),
]