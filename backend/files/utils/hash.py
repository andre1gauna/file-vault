import hashlib
from django.core.files.uploadedfile import UploadedFile
from django.db.models.fields.files import FieldFile

def sha256_from_uploaded(uploaded: UploadedFile, chunk_size: int = 8192) -> str:
    h = hashlib.sha256()
    for chunk in uploaded.chunks(chunk_size):
        h.update(chunk)
    return h.hexdigest()

def sha256_from_fieldfile(ff: FieldFile, chunk_size: int = 8192) -> str:
    h = hashlib.sha256()
    ff.open("rb")
    try:
        for chunk in ff.chunks(chunk_size):
            h.update(chunk)
    finally:
        ff.close()
    return h.hexdigest()