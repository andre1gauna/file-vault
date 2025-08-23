from ..models import StorageStats
from ..serializers import StorageStatsSerializer
from rest_framework import viewsets

class StorageStatsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StorageStats.objects.all()
    serializer_class = StorageStatsSerializer