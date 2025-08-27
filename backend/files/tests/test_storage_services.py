import pytest
from files.models import File, StorageStats
from files.services import storage_services
from .fixtures import create_file


@pytest.mark.django_db
def test_calculate_savings_updates_stats(create_file):
    File.objects.create(
        file=create_file("a.txt", b"abc"),
        original_filename="a.txt",
        size=100,
        file_type="text/plain",
        is_duplicate=False,
    )

    File.objects.create(
        file=create_file("b.txt", b"xyz"),
        original_filename="b.txt",
        size=100,
        file_type="text/plain",
        is_duplicate=True,
    )

    storage_services.calculate_savings()

    stats = StorageStats.objects.get(id=1)
    assert stats.total_files == 2
    assert stats.unique_files == 1
    assert stats.total_size == 200
    assert stats.actual_size == 100
    assert stats.storage_savings == 100

@pytest.mark.django_db
def test_calculate_distributions_returns_percentages(create_file):

    File.objects.create(
        file=create_file("small.txt", size=500),  # small (<1MB)
        original_filename="s.txt",
        size=500,
        file_type="text/plain",
        is_duplicate=False,
    )
    File.objects.create(
        file=create_file("medium.txt", size=2 * 1024 * 1024),  # medium (2MB)
        original_filename="m.txt",
        size=2 * 1024 * 1024,
        file_type="text/plain",
        is_duplicate=False,
    )
    File.objects.create(
        file=create_file("large.txt", size=20 * 1024 * 1024),  # large (20MB)
        original_filename="l.txt",
        size=20 * 1024 * 1024,
        file_type="text/plain",
        is_duplicate=False,
    )
    File.objects.create(
        file=create_file("huge.txt", size=150 * 1024 * 1024),  # huge (150MB)
        original_filename="h.txt",
        size=150 * 1024 * 1024,
        file_type="text/plain",
        is_duplicate=False,
    )

    dist = storage_services.calculate_distributions()

    assert dist["small"]["count"] == 1
    assert dist["medium"]["count"] == 1
    assert dist["large"]["count"] == 1
    assert dist["huge"]["count"] == 1
    assert round(sum(r["percentage"] for r in dist.values()), 2) == 100.0

