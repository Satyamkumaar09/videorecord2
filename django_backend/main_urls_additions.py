from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ... your existing URL patterns ...
    
    # Video tracker API
    path('', include('video_tracker.urls')),
    
    # Serve media files in development
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)