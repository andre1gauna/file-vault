from rest_framework import serializers
from .models import File, StorageStats

class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = [
            'id', 'file', 'original_filename', 'file_type', 'size', 
            'uploaded_at', 'file_hash', 'is_duplicate', 'original_file', 
            'reference_count'
        ]
        read_only_fields = ['id', 'uploaded_at', 'file_hash', 'is_duplicate', 'original_file', 'reference_count']

class StorageStatsSerializer(serializers.ModelSerializer):
    savings_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = StorageStats
        fields = [
            'total_files', 'unique_files', 'total_size', 'actual_size', 
            'storage_savings', 'savings_percentage', 'last_updated'
        ]
        read_only_fields = ['last_updated'] 