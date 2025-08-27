import pytest
from django.core.files.base import ContentFile
from files.models import File, StorageStats
from files.services import storage_services
from .fixtures import create_file


@pytest.mark.django_db
def test_calculate_savings_no_files():
    storage_services.calculate_savings()
    stats = StorageStats.objects.get(id=1)
    assert stats.total_files == 0
    assert stats.unique_files == 0
    assert stats.total_size == 0
    assert stats.actual_size == 0
    assert stats.storage_savings == 0


@pytest.mark.django_db
def test_calculate_savings_with_duplicates(create_file):
    File.objects.create(
        file=create_file("a.txt", b"abc"),
        original_filename="a.txt",
        size=3,
        file_type="text/plain",
        is_duplicate=False,
    )
    File.objects.create(
        file=create_file("b.txt", b"xyz"),
        original_filename="b.txt",
        size=3,
        file_type="text/plain",
        is_duplicate=True,
    )

    storage_services.calculate_savings()
    stats = StorageStats.objects.get(id=1)
    assert stats.total_files == 2
    assert stats.unique_files == 1
    assert stats.total_size == 6
    assert stats.actual_size == 3
    assert stats.storage_savings == 3


@pytest.mark.django_db
def test_calculate_distributions_empty():
    dist = storage_services.calculate_distributions()
    assert dist == {}


@pytest.mark.django_db
def test_calculate_distributions_all_ranges(create_file):
    # small (< 1MB)
    File.objects.create(
        file=create_file("small.txt", b"x" * 100),
        original_filename="small.txt",
        size=100,
        file_type="text/plain",
    )
    # medium (1MB–10MB)
    File.objects.create(
        file=create_file("medium.txt", b"x" * (2 * 1024 * 1024)),
        original_filename="medium.txt",
        size=2 * 1024 * 1024,
        file_type="text/plain",
    )
    # large (10MB–100MB)
    File.objects.create(
        file=create_file("large.txt", b"x" * (20 * 1024 * 1024)),
        original_filename="large.txt",
        size=20 * 1024 * 1024,
        file_type="application/octet-stream",
    )
    # huge (>= 100MB)
    File.objects.create(
        file=create_file("huge.txt", b"x" * (120 * 1024 * 1024)),
        original_filename="huge.txt",
        size=120 * 1024 * 1024,
        file_type="application/octet-stream",
    )

    dist = storage_services.calculate_distributions()

    assert dist["small"]["count"] == 1
    assert dist["medium"]["count"] == 1
    assert dist["large"]["count"] == 1
    assert dist["huge"]["count"] == 1
    total_percentage = sum(d["percentage"] for d in dist.values())
    assert round(total_percentage, 2) == 100.0
