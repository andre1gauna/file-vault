# backend/files/tests/conftest.py (ou no arquivo de testes)
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
    # Força MEDIA_ROOT para um diretório temporário único
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

        return ContentFile(data, name=name)  # compatível com FileField

    yield _create_file

    # 🔥 Cleanup: remove toda a pasta MEDIA_ROOT
    if tmp_path.exists():
        shutil.rmtree(tmp_path)
