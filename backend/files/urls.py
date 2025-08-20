from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FileViewSet, StorageStatsViewSet

router = DefaultRouter()
router.register(r'files', FileViewSet)
router.register(r'stats', StorageStatsViewSet, basename='storage-stats')

urlpatterns = [
    path('', include(router.urls)),
] 