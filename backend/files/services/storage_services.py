from ..models import File
from ..models import StorageStats

def calculate_savings():
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

def calculate_distributions():
    total_files = File.objects.count()
    if total_files == 0:
        return {}
    
    size_ranges = {
        'small': (0, 1024 * 1024),
        'medium': (1024 * 1024, 10 * 1024 * 1024),
        'large': (10 * 1024 * 1024, 100 * 1024 * 1024),
        'huge': (100 * 1024 * 1024, float('inf'))
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
    
    return distribution   # <-- fora do loop
