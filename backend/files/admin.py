from django.contrib import admin
from .models import File, StorageStats

@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = [
        'original_filename', 'file_type', 'size', 'uploaded_at', 
        'is_duplicate', 'reference_count'
    ]
    list_filter = ['file_type', 'is_duplicate', 'uploaded_at']
    search_fields = ['original_filename', 'file_type']
    readonly_fields = ['id', 'file_hash', 'uploaded_at', 'is_duplicate', 'original_file', 'reference_count']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('original_file')

@admin.register(StorageStats)
class StorageStatsAdmin(admin.ModelAdmin):
    list_display = [
        'total_files', 'unique_files', 'total_size', 
        'actual_size', 'storage_savings', 'savings_percentage', 'last_updated'
    ]
    readonly_fields = ['last_updated']
    
    def has_add_permission(self, request):
        return not StorageStats.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False
