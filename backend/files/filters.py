from django.utils import timezone
from django_filters import rest_framework as django_filters
from datetime import  timedelta
from .models import File

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