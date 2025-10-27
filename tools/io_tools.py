"""
I/O Tools: funções para os agentes reportarem progresso e salvarem artefatos.
Todas as funções retornam dict com status e informações.
"""

import base64
import json
import os
import zipfile
from pathlib import Path
from typing import Any

import requests

from tools.artifact_store import get_store, Artifact


def report_progress(stage: str, message: str) -> dict[str, Any]:
    """
    Reporta progresso ao longo da execução.
    
    Args:
        stage: Nome da etapa/fase atual (ex: "Análise", "Implementação")
        message: Mensagem descritiva do progresso
    
    Returns:
        dict com status e confirmação
    """
    store = get_store()
    store.log_progress(stage, message)
    print(f"[{stage}] {message}")
    return {"status": "ok", "stage": stage, "message": message}


def create_folder(relative_path: str) -> dict[str, Any]:
    """
    Cria uma pasta dentro do run_dir.
    
    Args:
        relative_path: Caminho relativo dentro do run_dir
    
    Returns:
        dict com status e caminho absoluto
    """
    store = get_store()
    folder_path = store.run_dir / relative_path
    folder_path.mkdir(parents=True, exist_ok=True)
    
    return {
        "status": "ok",
        "folder": str(folder_path.absolute()),
        "relative_path": relative_path
    }


def save_text(name: str, content: str, relative_path: str = "") -> dict[str, Any]:
    """
    Salva arquivo de texto (.txt).
    
    Args:
        name: Nome do arquivo (com ou sem extensão)
        content: Conteúdo do texto
        relative_path: Subpasta dentro do run_dir (opcional)
    
    Returns:
        dict com status e caminho do arquivo
    """
    store = get_store()
    
    if not name.endswith(".txt"):
        name = f"{name}.txt"
    
    if relative_path:
        target_dir = store.run_dir / relative_path
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / name
    else:
        file_path = store.run_dir / name
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    artifact = Artifact(
        name=name,
        kind="text",
        path=str(file_path.absolute()),
        meta={"size_bytes": len(content.encode("utf-8"))}
    )
    store.add(artifact)
    
    return {
        "status": "ok",
        "file": str(file_path.absolute()),
        "name": name,
        "kind": "text"
    }


def save_markdown(name: str, markdown: str, relative_path: str = "") -> dict[str, Any]:
    """
    Salva arquivo Markdown (.md).
    
    Args:
        name: Nome do arquivo (com ou sem extensão)
        markdown: Conteúdo Markdown
        relative_path: Subpasta dentro do run_dir (opcional)
    
    Returns:
        dict com status e caminho do arquivo
    """
    store = get_store()
    
    if not name.endswith(".md"):
        name = f"{name}.md"
    
    if relative_path:
        target_dir = store.run_dir / relative_path
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / name
    else:
        file_path = store.run_dir / name
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(markdown)
    
    artifact = Artifact(
        name=name,
        kind="markdown",
        path=str(file_path.absolute()),
        meta={"size_bytes": len(markdown.encode("utf-8"))}
    )
    store.add(artifact)
    
    return {
        "status": "ok",
        "file": str(file_path.absolute()),
        "name": name,
        "kind": "markdown"
    }


def save_json(name: str, data: dict | None = None, content: dict | None = None, relative_path: str = "") -> dict[str, Any]:
    """
    Salva arquivo JSON (.json).
    
    Args:
        name: Nome do arquivo (com ou sem extensão)
        data: Dicionário a ser serializado (aceita 'data' ou 'content')
        content: Alias para 'data' (para compatibilidade)
        relative_path: Subpasta dentro do run_dir (opcional)
    
    Returns:
        dict com status e caminho do arquivo
    """
    store = get_store()
    
    # Aceitar tanto 'data' quanto 'content'
    json_data = data if data is not None else content
    if json_data is None:
        return {
            "status": "error",
            "error": "Parâmetro 'data' ou 'content' é obrigatório"
        }
    
    if not name.endswith(".json"):
        name = f"{name}.json"
    
    if relative_path:
        target_dir = store.run_dir / relative_path
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / name
    else:
        file_path = store.run_dir / name
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    artifact = Artifact(
        name=name,
        kind="json",
        path=str(file_path.absolute()),
        meta={"keys": list(json_data.keys()) if isinstance(json_data, dict) else None}
    )
    store.add(artifact)
    
    return {
        "status": "ok",
        "file": str(file_path.absolute()),
        "name": name,
        "kind": "json"
    }


def save_file_from_url(
    url: str,
    name: str | None = None,
    relative_path: str = "",
    timeout: int = 20
) -> dict[str, Any]:
    """
    Baixa arquivo de URL e salva no run_dir.
    
    Args:
        url: URL do arquivo
        name: Nome do arquivo (opcional, extrai da URL se não fornecido)
        relative_path: Subpasta dentro do run_dir (opcional)
        timeout: Timeout em segundos para o download
    
    Returns:
        dict com status e caminho do arquivo
    """
    store = get_store()
    
    try:
        response = requests.get(url, timeout=timeout, stream=True)
        response.raise_for_status()
        
        if name is None:
            name = url.split("/")[-1] or "downloaded_file"
        
        if relative_path:
            target_dir = store.run_dir / relative_path
            target_dir.mkdir(parents=True, exist_ok=True)
            file_path = target_dir / name
        else:
            file_path = store.run_dir / name
        
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        file_size = file_path.stat().st_size
        
        artifact = Artifact(
            name=name,
            kind="file",
            path=str(file_path.absolute()),
            meta={"source_url": url, "size_bytes": file_size}
        )
        store.add(artifact)
        
        return {
            "status": "ok",
            "file": str(file_path.absolute()),
            "name": name,
            "kind": "file",
            "source_url": url,
            "size_bytes": file_size
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "url": url
        }


def save_base64(name: str, b64_content: str, relative_path: str = "") -> dict[str, Any]:
    """
    Decodifica conteúdo base64 e salva como arquivo.
    
    Args:
        name: Nome do arquivo
        b64_content: Conteúdo em base64
        relative_path: Subpasta dentro do run_dir (opcional)
    
    Returns:
        dict com status e caminho do arquivo
    """
    store = get_store()
    
    try:
        content_bytes = base64.b64decode(b64_content)
        
        if relative_path:
            target_dir = store.run_dir / relative_path
            target_dir.mkdir(parents=True, exist_ok=True)
            file_path = target_dir / name
        else:
            file_path = store.run_dir / name
        
        with open(file_path, "wb") as f:
            f.write(content_bytes)
        
        artifact = Artifact(
            name=name,
            kind="file",
            path=str(file_path.absolute()),
            meta={"size_bytes": len(content_bytes), "encoding": "base64"}
        )
        store.add(artifact)
        
        return {
            "status": "ok",
            "file": str(file_path.absolute()),
            "name": name,
            "kind": "file",
            "size_bytes": len(content_bytes)
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "name": name
        }


def list_artifacts() -> dict[str, Any]:
    """
    Lista todos os artefatos registrados até o momento.
    
    Returns:
        dict com lista de artefatos
    """
    store = get_store()
    artifacts = store.list()
    
    return {
        "status": "ok",
        "count": len(artifacts),
        "artifacts": artifacts
    }


def zip_run(name: str = "bundle.zip") -> dict[str, Any]:
    """
    Cria arquivo ZIP com todos os artefatos do run_dir.
    
    Args:
        name: Nome do arquivo ZIP
    
    Returns:
        dict com status e caminho do ZIP
    """
    store = get_store()
    
    if not name.endswith(".zip"):
        name = f"{name}.zip"
    
    zip_path = store.run_dir / name
    
    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(store.run_dir):
                for file in files:
                    if file == name:  # Não incluir o próprio ZIP
                        continue
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(store.run_dir)
                    zipf.write(file_path, arcname)
        
        zip_size = zip_path.stat().st_size
        
        artifact = Artifact(
            name=name,
            kind="zip",
            path=str(zip_path.absolute()),
            meta={"size_bytes": zip_size}
        )
        store.add(artifact)
        
        return {
            "status": "ok",
            "file": str(zip_path.absolute()),
            "name": name,
            "kind": "zip",
            "size_bytes": zip_size
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "name": name
        }


def finalize_run() -> dict[str, Any]:
    """
    Finaliza a run gerando MANIFEST.md com lista de artefatos.
    
    Returns:
        dict com status e caminho do MANIFEST
    """
    store = get_store()
    manifest_path = store.finalize_manifest()
    
    return {
        "status": "ok",
        "manifest": manifest_path,
        "run_dir": str(store.run_dir.absolute()),
        "artifact_count": len(store.artifacts)
    }

