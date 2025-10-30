#!/usr/bin/env python3
"""
Execution Memory - Aprende com execuções anteriores.

Funcionalidades:
- Salva histórico de execuções
- Identifica padrões de sucesso/falha
- Reutiliza soluções que funcionaram
- Aprende com erros
- Sugere melhorias baseadas em histórico
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import hashlib


class ExecutionMemory:
    """Sistema de memória para aprender com execuções."""
    
    def __init__(self, db_path: Path = None):
        if db_path is None:
            db_path = Path(__file__).parent.parent / 'memory' / 'executions.db'
        
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_database()
    
    def _init_database(self):
        """Inicializa banco de dados SQLite."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de execuções
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_description TEXT NOT NULL,
                task_hash TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                output_dir TEXT NOT NULL,
                success BOOLEAN NOT NULL,
                validation_passed BOOLEAN,
                total_artifacts INTEGER,
                execution_time_seconds REAL,
                agents_used TEXT,
                errors TEXT,
                metadata TEXT
            )
        ''')
        
        # Tabela de artefatos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS artifacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_id INTEGER NOT NULL,
                agent_name TEXT NOT NULL,
                filename TEXT NOT NULL,
                artifact_type TEXT NOT NULL,
                file_size INTEGER,
                file_hash TEXT,
                content_preview TEXT,
                FOREIGN KEY (execution_id) REFERENCES executions(id)
            )
        ''')
        
        # Tabela de aprendizados
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_pattern TEXT NOT NULL,
                learning_type TEXT NOT NULL,
                description TEXT NOT NULL,
                confidence_score REAL,
                times_applied INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        
        # Índices para performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_task_hash ON executions(task_hash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_success ON executions(success)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON executions(timestamp)')
        
        conn.commit()
        conn.close()
    
    def _hash_task(self, task_description: str) -> str:
        """Gera hash da tarefa para identificar similares."""
        # Normalizar: lowercase, remover pontuação extra
        normalized = task_description.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def save_execution(
        self,
        task_description: str,
        output_dir: Path,
        success: bool,
        validation_passed: bool = None,
        total_artifacts: int = 0,
        execution_time: float = 0,
        agents_used: List[str] = None,
        errors: List[str] = None,
        metadata: Dict = None
    ) -> int:
        """
        Salva execução no histórico.
        
        Returns:
            execution_id
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        task_hash = self._hash_task(task_description)
        timestamp = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO executions (
                task_description, task_hash, timestamp, output_dir,
                success, validation_passed, total_artifacts, execution_time_seconds,
                agents_used, errors, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            task_description,
            task_hash,
            timestamp,
            str(output_dir),
            success,
            validation_passed,
            total_artifacts,
            execution_time,
            json.dumps(agents_used) if agents_used else None,
            json.dumps(errors) if errors else None,
            json.dumps(metadata) if metadata else None
        ))
        
        execution_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"💾 Execução salva no histórico (ID: {execution_id})")
        
        return execution_id
    
    def save_artifacts(
        self,
        execution_id: int,
        artifacts: List[Dict]
    ):
        """Salva artefatos de uma execução."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for artifact in artifacts:
            # Calcular hash do arquivo
            file_hash = None
            content_preview = None
            
            if 'path' in artifact and Path(artifact['path']).exists():
                filepath = Path(artifact['path'])
                try:
                    with open(filepath, 'rb') as f:
                        file_hash = hashlib.md5(f.read()).hexdigest()
                    
                    # Preview do conteúdo (primeiros 500 chars)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content_preview = f.read(500)
                except:
                    pass
            
            cursor.execute('''
                INSERT INTO artifacts (
                    execution_id, agent_name, filename, artifact_type,
                    file_size, file_hash, content_preview
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                execution_id,
                artifact.get('agent', 'unknown'),
                artifact.get('filename', ''),
                artifact.get('type', 'unknown'),
                artifact.get('size', 0),
                file_hash,
                content_preview
            ))
        
        conn.commit()
        conn.close()
        
        print(f"💾 {len(artifacts)} artefatos salvos")
    
    def find_similar_executions(
        self,
        task_description: str,
        limit: int = 5
    ) -> List[Dict]:
        """
        Encontra execuções similares no histórico.
        
        Returns:
            Lista de execuções similares ordenadas por sucesso
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Buscar por hash exato primeiro
        task_hash = self._hash_task(task_description)
        
        cursor.execute('''
            SELECT id, task_description, timestamp, output_dir, success,
                   validation_passed, total_artifacts, execution_time_seconds
            FROM executions
            WHERE task_hash = ?
            ORDER BY success DESC, validation_passed DESC, timestamp DESC
            LIMIT ?
        ''', (task_hash, limit))
        
        exact_matches = cursor.fetchall()
        
        # Se não encontrar exatas, buscar por palavras-chave
        if not exact_matches:
            keywords = set(task_description.lower().split())
            # Buscar execuções que tenham pelo menos 2 palavras em comum
            cursor.execute('''
                SELECT id, task_description, timestamp, output_dir, success,
                       validation_passed, total_artifacts, execution_time_seconds
                FROM executions
                ORDER BY success DESC, timestamp DESC
                LIMIT 20
            ''')
            
            all_executions = cursor.fetchall()
            similar = []
            
            for exec_row in all_executions:
                exec_keywords = set(exec_row[1].lower().split())
                common = keywords & exec_keywords
                
                if len(common) >= 2:
                    similar.append(exec_row)
                
                if len(similar) >= limit:
                    break
            
            matches = similar
        else:
            matches = exact_matches
        
        conn.close()
        
        # Formatar resultados
        results = []
        for row in matches:
            results.append({
                'id': row[0],
                'task_description': row[1],
                'timestamp': row[2],
                'output_dir': row[3],
                'success': bool(row[4]),
                'validation_passed': bool(row[5]) if row[5] is not None else None,
                'total_artifacts': row[6],
                'execution_time': row[7]
            })
        
        return results
    
    def get_success_patterns(self, task_type: str = None) -> List[Dict]:
        """
        Identifica padrões de sucesso.
        
        Returns:
            Lista de padrões identificados
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Buscar execuções bem-sucedidas
        cursor.execute('''
            SELECT task_description, agents_used, total_artifacts, execution_time_seconds
            FROM executions
            WHERE success = 1 AND validation_passed = 1
            ORDER BY timestamp DESC
            LIMIT 50
        ''')
        
        successful = cursor.fetchall()
        conn.close()
        
        if not successful:
            return []
        
        # Analisar padrões
        patterns = []
        
        # Padrão: agentes mais usados em sucessos
        agents_count = {}
        for row in successful:
            if row[1]:
                agents = json.loads(row[1])
                for agent in agents:
                    agents_count[agent] = agents_count.get(agent, 0) + 1
        
        if agents_count:
            most_common_agents = sorted(agents_count.items(), key=lambda x: x[1], reverse=True)[:3]
            patterns.append({
                'type': 'successful_agents',
                'description': f"Agentes mais usados em sucessos: {', '.join(a[0] for a in most_common_agents)}",
                'confidence': 0.8
            })
        
        # Padrão: número médio de artefatos
        avg_artifacts = sum(row[2] for row in successful) / len(successful)
        patterns.append({
            'type': 'artifact_count',
            'description': f"Execuções bem-sucedidas geram em média {avg_artifacts:.1f} artefatos",
            'confidence': 0.7
        })
        
        return patterns
    
    def learn_from_failures(self) -> List[str]:
        """
        Analisa falhas para gerar aprendizados.
        
        Returns:
            Lista de lições aprendidas
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT task_description, errors, metadata
            FROM executions
            WHERE success = 0
            ORDER BY timestamp DESC
            LIMIT 20
        ''')
        
        failures = cursor.fetchall()
        conn.close()
        
        if not failures:
            return ["Nenhuma falha registrada ainda"]
        
        lessons = []
        
        # Analisar erros comuns
        error_types = {}
        for row in failures:
            if row[1]:
                errors = json.loads(row[1])
                for error in errors:
                    # Extrair tipo de erro
                    error_type = error.split(':')[0] if ':' in error else error[:50]
                    error_types[error_type] = error_types.get(error_type, 0) + 1
        
        if error_types:
            most_common = sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:3]
            for error_type, count in most_common:
                lessons.append(
                    f"Erro comum ({count}x): {error_type} - revisar validações e error handling"
                )
        
        return lessons
    
    def get_statistics(self) -> Dict:
        """Retorna estatísticas gerais."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total de execuções
        cursor.execute('SELECT COUNT(*) FROM executions')
        total = cursor.fetchone()[0]
        
        # Sucessos
        cursor.execute('SELECT COUNT(*) FROM executions WHERE success = 1')
        successes = cursor.fetchone()[0]
        
        # Validações passadas
        cursor.execute('SELECT COUNT(*) FROM executions WHERE validation_passed = 1')
        validated = cursor.fetchone()[0]
        
        # Tempo médio
        cursor.execute('SELECT AVG(execution_time_seconds) FROM executions WHERE execution_time_seconds > 0')
        avg_time = cursor.fetchone()[0] or 0
        
        # Total de artefatos
        cursor.execute('SELECT SUM(total_artifacts) FROM executions')
        total_artifacts = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_executions': total,
            'successful': successes,
            'success_rate': (successes / total * 100) if total > 0 else 0,
            'validated': validated,
            'validation_rate': (validated / total * 100) if total > 0 else 0,
            'avg_execution_time': avg_time,
            'total_artifacts_generated': total_artifacts
        }
    
    def print_statistics(self):
        """Imprime estatísticas formatadas."""
        stats = self.get_statistics()
        
        print("\n📊 ESTATÍSTICAS DO HISTÓRICO")
        print("=" * 80)
        print(f"Total de Execuções: {stats['total_executions']}")
        print(f"Sucessos: {stats['successful']} ({stats['success_rate']:.1f}%)")
        print(f"Validações Passadas: {stats['validated']} ({stats['validation_rate']:.1f}%)")
        print(f"Tempo Médio: {stats['avg_execution_time']:.1f}s")
        print(f"Total de Artefatos: {stats['total_artifacts_generated']}")
        print("=" * 80)


if __name__ == "__main__":
    # Teste básico
    memory = ExecutionMemory()
    memory.print_statistics()

