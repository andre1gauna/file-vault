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
    
    # Verifica se já existe um arquivo original com este hash
    existing_original = File.objects.filter(file_hash=file_hash, is_duplicate=False).first()
    
    if existing_original:
        # Incrementa a contagem de referências no arquivo original
        File.objects.filter(pk=existing_original.pk).update(
            reference_count=F("reference_count") + 1
        )
        
        # Gera um nome único para o arquivo físico
        import os
        from django.utils import timezone
        
        # Obtém a extensão do arquivo original
        original_name = getattr(file_obj, "name", "")
        _, ext = os.path.splitext(original_name)
        
        # Cria um nome único para o arquivo físico
        unique_filename = f"duplicate_{timezone.now().timestamp()}{ext}"
        
        # Cria o registro do arquivo duplicado
        duplicate = File.objects.create(
            file=file_obj,  # O arquivo físico será salvo com o nome único
            original_filename=original_name,
            size=getattr(file_obj, "size", 0),
            file_type=getattr(file_obj, "content_type", ""),
            is_duplicate=True,
            original_file=existing_original,
            # Não definimos file_hash para duplicatas, apenas o original tem o hash
        )
        
        # Renomeia o arquivo físico para o nome único
        if duplicate.file:
            current_path = duplicate.file.path
            new_path = os.path.join(os.path.dirname(current_path), unique_filename)
            os.rename(current_path, new_path)
            duplicate.file.name = os.path.join(os.path.dirname(duplicate.file.name), unique_filename)
            duplicate.save(update_fields=['file'])
        
        calculate_savings()
        return duplicate, {
            "message": "File is duplicate, reference created",
            "duplicate_of": existing_original.id,
            "is_duplicate": True
        }
    
    # Se não for duplicata, cria um novo arquivo original
    new_file = File(
        file=file_obj,
        original_filename=getattr(file_obj, "name", ""),
        size=getattr(file_obj, "size", 0),
        file_type=getattr(file_obj, "content_type", ""),
        is_duplicate=False,
        file_hash=file_hash,  # Apenas originais têm file_hash
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
