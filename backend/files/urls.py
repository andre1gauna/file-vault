from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.file_views import FileViewSet
from .views.stats_views import StorageStatsViewSet

router = DefaultRouter()
router.register(r'files', FileViewSet, basename='files')
router.register(r'stats', StorageStatsViewSet, basename='storage-stats')

urlpatterns = [
    path('', include(router.urls)),
] 