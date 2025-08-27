import pytest
from files.models import File, StorageStats
from files.serializers import FileSerializer, StorageStatsSerializer
from .fixtures import create_file


@pytest.mark.django_db
def test_file_serializer_readonly_fields(create_file):
    file_obj = File.objects.create(
        file=create_file("ser.txt", content=b"abc"),
        original_filename="ser.txt",
        file_type="text/plain",
        size=3,
        is_duplicate=False,
    )

    serializer = FileSerializer(file_obj)
    data = serializer.data

    assert "id" in data
    assert "original_filename" in data
    assert data["original_filename"] == "ser.txt"

    readonly = FileSerializer.Meta.read_only_fields
    for field in readonly:
        assert field in data


@pytest.mark.django_db
def test_storage_stats_serializer_includes_percentage():
    stats = StorageStats.objects.create(
        total_files=2,
        unique_files=1,
        total_size=100,
        actual_size=50,
        storage_savings=50,
    )

    serializer = StorageStatsSerializer(stats)
    data = serializer.data

    assert data["total_files"] == 2
    assert data["storage_savings"] == 50
    assert data["savings_percentage"] == 50.0
    assert "last_updated" in data
