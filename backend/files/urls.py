from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.file_views import FileViewSet
from .views.stats_views import StorageStatsViewSet

router = DefaultRouter()
router.register(r'files', FileViewSet, basename='file')
router.register(r'stats', StorageStatsViewSet, basename='storagestats')


urlpatterns = [
    path('', include(router.urls)),
] 