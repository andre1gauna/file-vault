from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from django.utils import timezone
from django_filters import rest_framework as django_filters
from django.db.models import Q
from datetime import datetime, timedelta
from .models import File, StorageStats
from .serializers import FileSerializer, StorageStatsSerializer
import hashlib

class FileFilter(django_filters.FilterSet):
    """Filter for File model"""
    filename = django_filters.CharFilter(field_name='original_filename', lookup_expr='icontains')
    file_type = django_filters.CharFilter(field_name='file_type', lookup_expr='icontains')
    size_min = django_filters.NumberFilter(field_name='size', lookup_expr='gte')
    size_max = django_filters.NumberFilter(field_name='size', lookup_expr='lte')
    uploaded_after = django_filters.DateTimeFilter(field_name='uploaded_at', lookup_expr='gte')
    uploaded_before = django_filters.DateTimeFilter(field_name='uploaded_at', lookup_expr='lte')
    is_duplicate = django_filters.BooleanFilter(field_name='is_duplicate')
    
    # Date range shortcuts
    today = django_filters.BooleanFilter(method='filter_today')
    this_week = django_filters.BooleanFilter(method='filter_this_week')
    this_month = django_filters.BooleanFilter(method='filter_this_month')
    
    class Meta:
        model = File
        fields = {
            'size': ['gte', 'lte'],
            'uploaded_at': ['gte', 'lte'],
        }
    
    def filter_today(self, queryset, name, value):
        if value:
            today = timezone.now().date()
            return queryset.filter(uploaded_at__date=today)
        return queryset
    
    def filter_this_week(self, queryset, name, value):
        if value:
            today = timezone.now().date()
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            return queryset.filter(uploaded_at__date__range=[week_start, week_end])
        return queryset
    
    def filter_this_month(self, queryset, name, value):
        if value:
            today = timezone.now().date()
            month_start = today.replace(day=1)
            if today.month == 12:
                month_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                month_end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
            return queryset.filter(uploaded_at__date__range=[month_start, month_end])
        return queryset

class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer
    filter_backends = [django_filters.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = FileFilter
    search_fields = ['original_filename', 'file_type']
    ordering_fields = ['original_filename', 'size', 'uploaded_at', 'file_type']
    ordering = ['-uploaded_at']

    def create(self, request, *args, **kwargs):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate file hash
        hash_sha256 = hashlib.sha256()
        for chunk in file_obj.chunks():
            hash_sha256.update(chunk)
        file_hash = hash_sha256.hexdigest()
        
        # Check for duplicate
        existing_file = File.objects.filter(file_hash=file_hash).first()
        
        if existing_file:
            # File is duplicate - create reference instead of saving
            with transaction.atomic():
                # Increment reference count on original file
                existing_file.reference_count += 1
                existing_file.save()
                
                # Create duplicate record
                duplicate_file = File.objects.create(
                    file=file_obj,
                    original_filename=file_obj.name,
                    file_type=file_obj.content_type,
                    size=file_obj.size,
                    file_hash=file_hash,
                    is_duplicate=True,
                    original_file=existing_file,
                    reference_count=1
                )
                
                # Update storage stats
                self._update_storage_stats()
                
                serializer = self.get_serializer(duplicate_file)
                return Response({
                    'message': 'File is duplicate, reference created',
                    'duplicate_of': existing_file.id,
                    'file': serializer.data
                }, status=status.HTTP_201_CREATED)
        else:
            # New unique file
            data = {
                'file': file_obj,
                'original_filename': file_obj.name,
                'file_type': file_obj.content_type,
                'size': file_obj.size,
                'file_hash': file_hash
            }
            
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            # Update storage stats
            self._update_storage_stats()
            
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        with transaction.atomic():
            if instance.is_duplicate:
                # Decrement reference count on original file
                if instance.original_file:
                    original = instance.original_file
                    original.reference_count = max(0, original.reference_count - 1)
                    original.save()
                    
            else:
                # Delete the actual file and all its duplicates
                if instance.file:
                    instance.file.delete(save=False)
                instance.duplicates.all().delete()
            
            instance.delete()
            
            # Update storage stats
            self._update_storage_stats()
            
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _update_storage_stats(self):
        """Update storage statistics"""
        total_files = File.objects.count()
        unique_files = File.objects.filter(is_duplicate=False).count()
        total_size = sum(file.size for file in File.objects.all())
        
        # Calculate actual size (unique files only)
        actual_size = sum(file.size for file in File.objects.filter(is_duplicate=False))
        # from django.db.models import Sum
        #actual_size =  File.objects.aggregate(total=Sum('size'))['total']
        storage_savings = total_size - actual_size
        
        # Update or create stats
        stats, created = StorageStats.objects.update_or_create(
            id=1,
            defaults={
                'total_files': total_files,
                'unique_files': unique_files,
                'total_size': total_size,
                'actual_size': actual_size,
                'storage_savings': storage_savings,
            }
        )

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
    def search(self, request):
        """Advanced search endpoint"""
        query = request.query_params.get('q', '')
        file_type = request.query_params.get('type', '')
        size_min = request.query_params.get('size_min')
        size_max = request.query_params.get('size_max')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        queryset = self.get_queryset()
        
        # Build search query
        if query:
            queryset = queryset.filter(
                Q(original_filename__icontains=query) |
                Q(file_type__icontains=query)
            )
        
        # Apply filters
        if file_type:
            queryset = queryset.filter(file_type__icontains=file_type)
        
        if size_min:
            queryset = queryset.filter(size__gte=size_min)
        
        if size_max:
            queryset = queryset.filter(size__lte=size_max)
        
        if date_from:
            queryset = queryset.filter(uploaded_at__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(uploaded_at__lte=date_to)
        
        # Pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def file_types(self, request):
        """Get list of available file types"""
        file_types = File.objects.values_list('file_type', flat=True).distinct()
        return Response(list(file_types))

    @action(detail=False, methods=['get'])
    def size_distribution(self, request):
        """Get file size distribution statistics"""
        total_files = File.objects.count()
        if total_files == 0:
            return Response({'message': 'No files found'})
        
        # Size ranges in bytes
        size_ranges = {
            'small': (0, 1024 * 1024),      # 0 - 1MB
            'medium': (1024 * 1024, 10 * 1024 * 1024),  # 1MB - 10MB
            'large': (10 * 1024 * 1024, 100 * 1024 * 1024),  # 10MB - 100MB
            'huge': (100 * 1024 * 1024, float('inf'))  # 100MB+
        }
        
        distribution = {}
        for range_name, (min_size, max_size) in size_ranges.items():
            if max_size == float('inf'):
                count = File.objects.filter(size__gte=min_size).count()
            else:
                count = File.objects.filter(size__gte=min_size, size__lt=max_size).count()
            distribution[range_name] = {
                'count': count,
                'percentage': round((count / total_files) * 100, 2)
            }
        
        return Response(distribution)

class StorageStatsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for storage statistics"""
    queryset = StorageStats.objects.all()
    serializer_class = StorageStatsSerializer
    
    def get_queryset(self):
        # Always return the latest stats
        return StorageStats.objects.filter(id=1)
