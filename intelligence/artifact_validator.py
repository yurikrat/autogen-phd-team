"""
Sistema de Validação Inteligente de Artefatos.
Garante que os artefatos criados fazem sentido para a tarefa.
"""

from typing import Dict, List, Any
from pathlib import Path
import json


class ArtifactValidator:
    """
    Valida se os artefatos criados fazem sentido para a tarefa solicitada.
    Funciona como um revisor humano experiente.
    """
    
    def __init__(self):
        self.validation_results = []
    
    def validate_artifacts_for_task(
        self,
        task: str,
        artifacts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Valida se os artefatos criados são adequados para a tarefa.
        
        Args:
            task: Descrição da tarefa original
            artifacts: Lista de artefatos criados
        
        Returns:
            Resultado da validação com score e feedback
        """
        task_lower = task.lower()
        
        # Identificar tipo de tarefa
        task_type = self._identify_task_type(task_lower)
        
        # Validar artefatos baseado no tipo de tarefa
        validation = {
            "task_type": task_type,
            "artifacts_count": len(artifacts),
            "expected_artifacts": self._get_expected_artifacts(task_type, task_lower),
            "found_artifacts": [a["name"] for a in artifacts],
            "missing_critical": [],
            "unexpected": [],
            "quality_issues": [],
            "score": 0.0,
            "feedback": []
        }
        
        # Verificar artefatos esperados
        for expected in validation["expected_artifacts"]:
            found = any(
                expected["pattern"].lower() in a["name"].lower()
                or expected["pattern"].lower() in a.get("kind", "").lower()
                for a in artifacts
            )
            
            if not found and expected["critical"]:
                validation["missing_critical"].append(expected["name"])
                validation["feedback"].append(
                    f"❌ CRÍTICO: Faltando {expected['name']} - {expected['reason']}"
                )
        
        # Verificar qualidade dos artefatos
        for artifact in artifacts:
            quality_issues = self._check_artifact_quality(artifact, task_type)
            validation["quality_issues"].extend(quality_issues)
        
        # Calcular score
        validation["score"] = self._calculate_score(validation)
        
        # Gerar feedback geral
        if validation["score"] >= 0.9:
            validation["feedback"].insert(0, "✅ EXCELENTE: Artefatos completos e de alta qualidade!")
        elif validation["score"] >= 0.7:
            validation["feedback"].insert(0, "✅ BOM: Artefatos adequados, mas pode melhorar.")
        elif validation["score"] >= 0.5:
            validation["feedback"].insert(0, "⚠️ REGULAR: Artefatos básicos, faltam componentes importantes.")
        else:
            validation["feedback"].insert(0, "❌ INSUFICIENTE: Artefatos não atendem a tarefa adequadamente.")
        
        self.validation_results.append(validation)
        return validation
    
    def _identify_task_type(self, task_lower: str) -> str:
        """Identifica o tipo de tarefa baseado em palavras-chave."""
        if any(kw in task_lower for kw in ["api", "rest", "endpoint", "backend"]):
            return "api_backend"
        elif any(kw in task_lower for kw in ["frontend", "react", "vue", "interface", "ui"]):
            return "frontend"
        elif any(kw in task_lower for kw in ["banco", "database", "schema", "modelo"]):
            return "database"
        elif any(kw in task_lower for kw in ["deploy", "ci/cd", "docker", "kubernetes"]):
            return "devops"
        elif any(kw in task_lower for kw in ["documentação", "docs", "manual"]):
            return "documentation"
        elif any(kw in task_lower for kw in ["teste", "test", "qa"]):
            return "testing"
        elif any(kw in task_lower for kw in ["arquitetura", "design", "diagrama"]):
            return "architecture"
        else:
            return "general"
    
    def _get_expected_artifacts(self, task_type: str, task_lower: str) -> List[Dict]:
        """Retorna artefatos esperados baseado no tipo de tarefa."""
        expected = {
            "api_backend": [
                {"name": "Código da API", "pattern": ".py", "critical": True, "reason": "API precisa de código"},
                {"name": "Documentação da API", "pattern": "api", "critical": True, "reason": "API precisa de docs"},
                {"name": "Testes", "pattern": "test", "critical": True, "reason": "API precisa de testes"},
                {"name": "Requirements", "pattern": "requirements", "critical": False, "reason": "Dependências devem estar documentadas"},
            ],
            "frontend": [
                {"name": "Componentes", "pattern": ".jsx", "critical": True, "reason": "Frontend precisa de componentes"},
                {"name": "Estilos", "pattern": ".css", "critical": True, "reason": "Frontend precisa de estilos"},
                {"name": "README", "pattern": "readme", "critical": False, "reason": "Instruções de uso"},
            ],
            "database": [
                {"name": "Schema SQL", "pattern": ".sql", "critical": True, "reason": "Banco precisa de schema"},
                {"name": "Diagrama ER", "pattern": "diagram", "critical": True, "reason": "Banco precisa de modelo visual"},
                {"name": "Documentação", "pattern": ".md", "critical": False, "reason": "Explicação do modelo"},
            ],
            "devops": [
                {"name": "Dockerfile", "pattern": "dockerfile", "critical": True, "reason": "Deploy precisa de container"},
                {"name": "CI/CD Config", "pattern": ".yml", "critical": True, "reason": "Automação precisa de pipeline"},
                {"name": "README", "pattern": "readme", "critical": False, "reason": "Instruções de deploy"},
            ],
            "documentation": [
                {"name": "Documentação Principal", "pattern": ".md", "critical": True, "reason": "Docs precisam de conteúdo"},
                {"name": "Exemplos", "pattern": "example", "critical": False, "reason": "Docs precisam de exemplos"},
            ],
            "testing": [
                {"name": "Testes", "pattern": "test", "critical": True, "reason": "QA precisa de testes"},
                {"name": "Relatório", "pattern": "report", "critical": False, "reason": "Resultados devem ser documentados"},
            ],
            "architecture": [
                {"name": "Diagrama", "pattern": "diagram", "critical": True, "reason": "Arquitetura precisa de visual"},
                {"name": "Documentação", "pattern": ".md", "critical": True, "reason": "Decisões devem ser documentadas"},
            ],
            "general": [
                {"name": "Documentação", "pattern": ".md", "critical": False, "reason": "Sempre é bom ter docs"},
            ]
        }
        
        return expected.get(task_type, expected["general"])
    
    def _check_artifact_quality(self, artifact: Dict, task_type: str) -> List[str]:
        """Verifica qualidade de um artefato específico."""
        issues = []
        
        # Verificar se arquivo existe
        path = artifact.get("path")
        if path and Path(path).exists():
            file_size = Path(path).stat().st_size
            
            # Arquivo muito pequeno pode ser vazio ou incompleto
            if file_size < 100:
                issues.append(f"⚠️ {artifact['name']}: Arquivo muito pequeno ({file_size} bytes) - pode estar incompleto")
            
            # Verificar conteúdo se for texto
            if artifact.get("kind") in ["markdown", "json", "text", "python", "javascript"]:
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Verificar se tem conteúdo mínimo
                    if len(content.strip()) < 50:
                        issues.append(f"⚠️ {artifact['name']}: Conteúdo muito curto - parece incompleto")
                    
                    # Verificar se JSON é válido
                    if artifact.get("kind") == "json":
                        try:
                            json.loads(content)
                        except json.JSONDecodeError:
                            issues.append(f"❌ {artifact['name']}: JSON inválido")
                    
                    # Verificar se Markdown tem estrutura
                    if artifact.get("kind") == "markdown":
                        if "#" not in content:
                            issues.append(f"⚠️ {artifact['name']}: Markdown sem headers - falta estrutura")
                    
                    # Verificar se código tem imports/funções
                    if artifact.get("kind") in ["python", "javascript"]:
                        if "def " not in content and "function " not in content and "class " not in content:
                            issues.append(f"⚠️ {artifact['name']}: Código sem funções/classes - parece incompleto")
                
                except Exception as e:
                    issues.append(f"❌ {artifact['name']}: Erro ao ler arquivo - {str(e)}")
        else:
            issues.append(f"❌ {artifact['name']}: Arquivo não encontrado no caminho especificado")
        
        return issues
    
    def _calculate_score(self, validation: Dict) -> float:
        """Calcula score de qualidade dos artefatos (0.0 a 1.0)."""
        score = 1.0
        
        # Penalizar por artefatos críticos faltando
        critical_missing = len(validation["missing_critical"])
        score -= critical_missing * 0.3
        
        # Penalizar por problemas de qualidade
        quality_issues = len(validation["quality_issues"])
        score -= quality_issues * 0.1
        
        # Bonificar por ter artefatos esperados
        expected_count = len(validation["expected_artifacts"])
        found_count = len(validation["found_artifacts"])
        if expected_count > 0:
            coverage = found_count / expected_count
            score *= coverage
        
        return max(0.0, min(1.0, score))
    
    def generate_improvement_suggestions(self, validation: Dict) -> List[str]:
        """Gera sugestões de melhoria baseado na validação."""
        suggestions = []
        
        for missing in validation["missing_critical"]:
            suggestions.append(f"🔧 Criar {missing}")
        
        for issue in validation["quality_issues"]:
            if "muito pequeno" in issue or "muito curto" in issue:
                suggestions.append(f"🔧 Expandir conteúdo do arquivo mencionado")
            elif "JSON inválido" in issue:
                suggestions.append(f"🔧 Corrigir sintaxe do JSON")
            elif "sem headers" in issue:
                suggestions.append(f"🔧 Adicionar estrutura com headers no Markdown")
            elif "sem funções" in issue:
                suggestions.append(f"🔧 Implementar funções/classes no código")
        
        return suggestions


# Instância global
_validator = None

def get_validator() -> ArtifactValidator:
    """Retorna instância singleton do validador."""
    global _validator
    if _validator is None:
        _validator = ArtifactValidator()
    return _validator

