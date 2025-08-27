# backend/files/tests/test_file_service.py
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from files.models import File
from files.services import file_service


@pytest.mark.django_db
def test_create_new_file(monkeypatch):
    # Simula hash fixo
    monkeypatch.setattr("files.services.file_service.sha256_from_uploaded", lambda f: "fakehash123")

    file = SimpleUploadedFile("test.txt", b"content", content_type="text/plain")

    new_file, meta = file_service.create_or_update_file(file)

    assert new_file.id is not None
    assert new_file.file_hash == "fakehash123"
    assert meta["is_duplicate"] is False
    assert new_file.is_duplicate is False


@pytest.mark.django_db
def test_create_duplicate_file(monkeypatch):
    monkeypatch.setattr("files.services.file_service.sha256_from_uploaded", lambda f: "samehash")

    # Cria original
    original = File.objects.create(
        file="dummy.txt", original_filename="dummy.txt", file_type="text/plain",
        size=10, file_hash="samehash", is_duplicate=False, reference_count=1
    )

    file = SimpleUploadedFile("dup.txt", b"dup content", content_type="text/plain")

    duplicate, meta = file_service.create_or_update_file(file)

    assert duplicate.is_duplicate is True
    assert meta["is_duplicate"] is True
    assert meta["duplicate_of"] == original.id


@pytest.mark.django_db
def test_destroy_file_reduces_reference_count(monkeypatch):
    # Cria original
    original = File.objects.create(
        file="orig.txt", original_filename="orig.txt", file_type="text/plain",
        size=10, file_hash="hash1", is_duplicate=False, reference_count=1
    )
    duplicate = File.objects.create(
        file="dup.txt", original_filename="dup.txt", file_type="text/plain",
        size=10, file_hash="hash1", is_duplicate=True, original_file=original
    )

    file_service.destroy_file(duplicate)

    original.refresh_from_db()
    assert original.reference_count == 0
