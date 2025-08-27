import pytest
import os
import shutil
from django.core.files.base import ContentFile
from typing import Optional


@pytest.fixture
def create_file(settings, tmp_path):
    """
    Cria arquivos em MEDIA_ROOT e garante que o diretório inteiro
    seja limpo ao final do teste.
    """
    settings.MEDIA_ROOT = tmp_path

    def _create_file(name: str, content: Optional[bytes] = None, size: Optional[int] = None):
        if content is None and size is None:
            data = b"test-data"
        elif content is not None:
            data = content
        else:
            data = b"x" * size

        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)

        return ContentFile(data, name=name) 

    yield _create_file

    if tmp_path.exists():
        shutil.rmtree(tmp_path)
