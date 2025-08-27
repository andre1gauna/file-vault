from django.db import models
import uuid
import os
from .utils.hash import sha256_from_fieldfile

def file_upload_path(instance, filename):
    """Generate file path for new file upload"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('uploads', filename)

class File(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to=file_upload_path)
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=100)
    size = models.BigIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # Deduplication fields
    file_hash = models.CharField(max_length=64, db_index=True)  
    is_duplicate = models.BooleanField(default=False)
    original_file = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True, related_name='duplicates')
    reference_count = models.PositiveIntegerField(default=1) 
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return self.original_filename
    
    def calculate_hash(self):
        """Calculate SHA-256 hash of the file content"""
        return sha256_from_fieldfile(self.file)
    
    
    def save(self, *args, **kwargs):
        # Calculate hash before saving if not already set
        if not self.file_hash and self.file:
            self.file_hash = self.calculate_hash()
        super().save(*args, **kwargs)

class StorageStats(models.Model):
    """Track storage statistics and savings from deduplication"""
    total_files = models.PositiveIntegerField(default=0)
    unique_files = models.PositiveIntegerField(default=0)
    total_size = models.BigIntegerField(default=0)
    actual_size = models.BigIntegerField(default=0)  # Size after deduplication
    storage_savings = models.BigIntegerField(default=0)  # Bytes saved
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Storage Statistics"
    
    def __str__(self):
        return f"Storage Stats - {self.last_updated.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def savings_percentage(self):
        """Calculate storage savings as percentage"""
        if self.total_size == 0:
            return 0
        return round((self.storage_savings / self.total_size) * 100, 2)
