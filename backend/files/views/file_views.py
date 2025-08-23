from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from django_filters import rest_framework as django_filters
from ..models import File
from ..filters import FileFilter
from ..serializers import FileSerializer
from rest_framework.decorators import action
from django.db.models import Q
from ..services.file_service import create_or_update_file, destroy_file
from ..services.storage_services import calculate_distributions

class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer
    filter_backends = [django_filters.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = FileFilter
    search_fields = ['original_filename', 'file_type']
    ordering_fields = ['original_filename', 'size', 'uploaded_at', 'file_type']
    ordering = ['-uploaded_at']

    def create(self, request, *args, **kwargs):
        file_obj = request.FILES.get("file")
        try:
            file_instance, meta = create_or_update_file(file_obj)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(file_instance)
        data = serializer.data
        data.update(meta)

        headers = self.get_success_headers(serializer.data)
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)    

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        destroy_file(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'])
    def duplicates(self, request):
        """Get all duplicate files"""
        duplicates = File.objects.filter(is_duplicate=True)
        serializer = self.get_serializer(duplicates, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def unique(self, request):
        """Get all unique files"""
        unique_files = File.objects.filter(is_duplicate=False)
        serializer = self.get_serializer(unique_files, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def file_types(self, request):
        """Get list of available file types"""
        file_types = File.objects.values_list('file_type', flat=True).distinct()
        return Response(list(file_types))

    @action(detail=False, methods=['get'])
    def size_distribution(self, request):
        """Get file size distribution statistics"""
        distribution = calculate_distributions()
        if distribution == 0:
            return Response({'message': 'No files found'})
        return Response(distribution)

    