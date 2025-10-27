"""
ArtifactStore: gerencia artefatos gerados durante a execução do time de agentes.
Cria runs/<timestamp>/, mantém artifacts.json, progress.log e gera MANIFEST.md.
"""

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class Artifact:
    """Representa um artefato gerado durante a execução."""
    name: str
    kind: str  # 'text', 'markdown', 'json', 'file', 'zip', etc.
    path: str
    meta: dict[str, Any] | None = None


class ArtifactStore:
    """
    Gerencia artefatos em runs/<timestamp>/.
    Mantém artifacts.json, progress.log e gera MANIFEST.md.
    """

    def __init__(self, base_dir: str = "runs"):
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.run_dir = Path(base_dir) / timestamp
        self.run_dir.mkdir(parents=True, exist_ok=True)
        
        self.artifacts_file = self.run_dir / "artifacts.json"
        self.progress_file = self.run_dir / "progress.log"
        self.manifest_file = self.run_dir / "MANIFEST.md"
        
        self.artifacts: list[Artifact] = []
        self._save_artifacts()
        
        # Log inicial
        self._log(f"=== RUN INICIADA: {timestamp} ===\n")

    def add(self, artifact: Artifact) -> None:
        """Adiciona um artefato ao registro."""
        self.artifacts.append(artifact)
        self._save_artifacts()

    def list(self) -> list[dict]:
        """Retorna lista de artefatos como dicionários."""
        return [asdict(a) for a in self.artifacts]

    def _save_artifacts(self) -> None:
        """Salva artifacts.json."""
        with open(self.artifacts_file, "w", encoding="utf-8") as f:
            json.dump(self.list(), f, indent=2, ensure_ascii=False)

    def _log(self, message: str) -> None:
        """Adiciona entrada ao progress.log."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] {message}\n"
        with open(self.progress_file, "a", encoding="utf-8") as f:
            f.write(entry)

    def log_progress(self, stage: str, message: str) -> None:
        """Registra progresso com stage e mensagem."""
        self._log(f"[{stage}] {message}")

    def finalize_manifest(self) -> str:
        """
        Gera MANIFEST.md com lista de artefatos e registra como artefato.
        Retorna o caminho do MANIFEST.md.
        """
        lines = [
            "# MANIFEST - Artefatos Gerados\n",
            f"**Run Directory:** `{self.run_dir.absolute()}`\n",
            f"**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
            "\n## Artefatos\n"
        ]
        
        if not self.artifacts:
            lines.append("_Nenhum artefato gerado._\n")
        else:
            for i, artifact in enumerate(self.artifacts, 1):
                lines.append(f"### {i}. {artifact.name}\n")
                lines.append(f"- **Tipo:** {artifact.kind}\n")
                lines.append(f"- **Caminho:** `{artifact.path}`\n")
                if artifact.meta:
                    lines.append(f"- **Metadados:** {json.dumps(artifact.meta, ensure_ascii=False)}\n")
                lines.append("\n")
        
        lines.append("\n---\n")
        lines.append("_Gerado automaticamente pelo Finalizer._\n")
        
        manifest_content = "".join(lines)
        with open(self.manifest_file, "w", encoding="utf-8") as f:
            f.write(manifest_content)
        
        # Registra o próprio MANIFEST como artefato
        manifest_artifact = Artifact(
            name="MANIFEST.md",
            kind="manifest",
            path=str(self.manifest_file.absolute()),
            meta={"artifact_count": len(self.artifacts)}
        )
        self.artifacts.append(manifest_artifact)
        self._save_artifacts()
        
        return str(self.manifest_file.absolute())


# Singleton global (instanciado em team_runtime.py)
_store: ArtifactStore | None = None


def get_store() -> ArtifactStore:
    """Retorna a instância global do ArtifactStore."""
    if _store is None:
        raise RuntimeError("ArtifactStore não foi inicializado. Chame init_store() primeiro.")
    return _store


def init_store(base_dir: str = "runs") -> ArtifactStore:
    """Inicializa o ArtifactStore global."""
    global _store
    _store = ArtifactStore(base_dir)
    return _store

