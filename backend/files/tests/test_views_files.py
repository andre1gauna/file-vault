import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from files.models import File
from .fixtures import create_file


@pytest.mark.django_db
def test_create_file_success(create_file):
    client = APIClient()
    file_data = create_file("upload.txt", content=b"abc")

    url = reverse("file-list")  
    response = client.post(url, {"file": file_data}, format="multipart")

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "id" in data
    assert data["original_filename"] == "upload.txt"
    assert data["is_duplicate"] is False


@pytest.mark.django_db
def test_create_file_no_file_error():
    client = APIClient()
    url = reverse("file-list")
    response = client.post(url, {}, format="multipart")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "error" in response.json()


@pytest.mark.django_db
def test_destroy_file(create_file):
    client = APIClient()
    f = File.objects.create(
        file=create_file("delete.txt", content=b"abc"),
        original_filename="delete.txt",
        size=3,
        file_type="text/plain",
    )

    url = reverse("file-detail", args=[f.pk])
    response = client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert File.objects.count() == 0


@pytest.mark.django_db
def test_duplicates_and_unique(create_file):
    client = APIClient()

    f1 = File.objects.create(
        file=create_file("orig.txt", content=b"abc"),
        original_filename="orig.txt",
        size=3,
        file_type="text/plain",
        is_duplicate=False,
    )
    f2 = File.objects.create(
        file=create_file("dup.txt", content=b"abc"),
        original_filename="dup.txt",
        size=3,
        file_type="text/plain",
        is_duplicate=True,
        original_file=f1,
    )

    url_dup = reverse("file-duplicates")
    url_unique = reverse("file-unique")

    resp_dup = client.get(url_dup)
    resp_unique = client.get(url_unique)

    assert len(resp_dup.json()) == 1
    assert resp_dup.json()[0]["original_filename"] == "dup.txt"

    assert len(resp_unique.json()) == 1
    assert resp_unique.json()[0]["original_filename"] == "orig.txt"


@pytest.mark.django_db
def test_file_types(create_file):
    client = APIClient()
    File.objects.create(
        file=create_file("f.txt", content=b"abc"),
        original_filename="f.txt",
        size=3,
        file_type="text/plain",
    )
    File.objects.create(
        file=create_file("g.pdf", content=b"xyz"),
        original_filename="g.pdf",
        size=3,
        file_type="application/pdf",
    )

    url = reverse("file-file-types")
    resp = client.get(url)
    types = resp.json()

    assert "text/plain" in types
    assert "application/pdf" in types

