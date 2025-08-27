from django.db import transaction
from ..models import File
from .storage_services import calculate_savings
from ..utils.hash import sha256_from_uploaded
from django.db.models import F
from django.core.files.uploadedfile import UploadedFile

    

@transaction.atomic
def create_or_update_file(file_obj: UploadedFile) -> tuple[File, dict]:
    if not file_obj:
        raise ValueError("No file provided")

    # Primeiro, tenta encontrar um arquivo com o mesmo hash
    file_hash = sha256_from_uploaded(file_obj)
    
    # Encontra o arquivo original (se for uma duplicata, pega o original)
    original_file = File.objects.filter(file_hash=file_hash, is_duplicate=False).first()
    
    if original_file:
        # Incrementa a contagem de referências no arquivo original
        File.objects.filter(pk=original_file.pk).update(
            reference_count=F("reference_count") + 1
        )
        
        # Cria o registro do arquivo duplicado
        duplicate = File(
            file=file_obj,
            original_filename=getattr(file_obj, "name", ""),
            size=getattr(file_obj, "size", 0),
            file_type=getattr(file_obj, "content_type", ""),
            is_duplicate=True,
            original_file=original_file,
            file_hash=file_hash,
        )
        duplicate.save()
        
        calculate_savings()
        return duplicate, {
            "message": "File is duplicate, reference created",
            "duplicate_of": original_file.id,
            "is_duplicate": True
        }
    
    # Se não for duplicata, cria um novo arquivo original
    new_file = File(
        file=file_obj,
        original_filename=getattr(file_obj, "name", ""),
        size=getattr(file_obj, "size", 0),
        file_type=getattr(file_obj, "content_type", ""),
        is_duplicate=False,
        file_hash=file_hash,
        reference_count=0,
    )
    new_file.save()
    
    transaction.on_commit(calculate_savings)
    return new_file, {"is_duplicate": False}


@transaction.atomic
def destroy_file(file_obj: File) -> None:
    file_to_delete = file_obj.file if file_obj.file else None
    orig_id = getattr(file_obj, "original_file_id", None) 

    if file_obj.is_duplicate and orig_id:
        File.objects.filter(
            pk=orig_id,
            reference_count__gt=0
        ).update(reference_count=F("reference_count") - 1)

    file_obj.delete()
    transaction.on_commit(calculate_savings)

    if file_to_delete:
        transaction.on_commit(lambda: file_to_delete.delete(save=False))
