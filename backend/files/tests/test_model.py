import pytest
from files.models import File, StorageStats
from .fixtures import create_file


@pytest.mark.django_db
def test_file_str_and_hash(create_file):
    f = File.objects.create(
        file=create_file("hash.txt", content=b"hello world"),
        original_filename="hash.txt",
        file_type="text/plain",
        size=11,
        is_duplicate=False,
    )

    assert str(f) == "hash.txt"

    assert f.file_hash is not None
    assert len(f.file_hash) == 64  


@pytest.mark.django_db
def test_storage_stats_str_and_percentage():
    stats = StorageStats.objects.create(
        total_files=10,
        unique_files=5,
        total_size=1000,
        actual_size=600,
        storage_savings=400,
    )

    assert "Storage Stats" in str(stats)

    assert stats.savings_percentage == 40.0


@pytest.mark.django_db
def test_storage_stats_percentage_zero_division():
    stats = StorageStats.objects.create(
        total_files=0,
        unique_files=0,
        total_size=0,
        actual_size=0,
        storage_savings=0,
    )
    assert stats.savings_percentage == 0
