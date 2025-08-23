import hashlib

def calculate_file_hash(file_obj) -> str:
    """Calcula SHA256 usando sempre .chunks(), 
    funciona para UploadedFile e FieldFile."""
    hash_sha256 = hashlib.sha256()
    for chunk in file_obj.chunks():
        hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

