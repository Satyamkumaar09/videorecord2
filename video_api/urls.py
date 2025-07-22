from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VideoSessionViewSet

router = DefaultRouter()
router.register(r'sessions', VideoSessionViewSet)

urlpatterns = [
    path('api/video/', include(router.urls)),
]
