#!/usr/bin/env python3
"""
Dynamic Challenger - Gera desafios contextuais baseados em análise real do código.

Funcionalidades:
- Analisa código gerado
- Identifica pontos fracos específicos
- Gera perguntas contextuais (não genéricas)
- Força revisão e melhoria
"""

import ast
import re
from pathlib import Path
from typing import List, Dict
from openai import OpenAI
import os


class DynamicChallenger:
    """Gera desafios contextuais para forçar melhorias."""
    
    def __init__(self):
        self.client = OpenAI()  # API key já configurada no ambiente
    
    def analyze_and_challenge(self, artifact_path: Path, artifact_type: str) -> List[str]:
        """
        Analisa artefato e gera desafios específicos.
        
        Args:
            artifact_path: Caminho do arquivo
            artifact_type: Tipo (code, tests, docs, etc.)
            
        Returns:
            Lista de desafios específicos
        """
        print(f"\n🎯 Analisando {artifact_path.name} para gerar desafios...")
        
        # Ler conteúdo
        try:
            with open(artifact_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"   ❌ Erro ao ler arquivo: {e}")
            return []
        
        # Análise estática primeiro
        static_issues = self._static_analysis(content, artifact_type)
        
        # Gerar desafios contextuais com LLM
        contextual_challenges = self._generate_contextual_challenges(
            content, artifact_type, static_issues
        )
        
        return contextual_challenges
    
    def _static_analysis(self, content: str, artifact_type: str) -> List[str]:
        """Análise estática para identificar problemas óbvios."""
        issues = []
        
        if artifact_type == 'code':
            # Análise de código Python
            if content.strip():
                # Verificar imports
                if 'import' not in content:
                    issues.append("Sem imports - pode estar faltando dependências")
                
                # Verificar docstrings
                if '"""' not in content and "'''" not in content:
                    issues.append("Sem docstrings - falta documentação inline")
                
                # Verificar error handling
                if 'try:' not in content and 'except' not in content:
                    issues.append("Sem error handling - código pode falhar silenciosamente")
                
                # Verificar type hints
                if '->' not in content:
                    issues.append("Sem type hints - dificulta manutenção")
                
                # Verificar logging
                if 'logging' not in content and 'logger' not in content:
                    issues.append("Sem logging - dificulta debugging")
                
                # Verificar validação de inputs
                if 'raise' not in content and 'assert' not in content:
                    issues.append("Sem validação de inputs - vulnerável a dados inválidos")
        
        elif artifact_type == 'tests':
            # Análise de testes
            if 'def test_' not in content:
                issues.append("Sem funções de teste - arquivo pode não ser teste válido")
            
            if 'assert' not in content:
                issues.append("Sem assertions - testes não validam nada")
            
            # Contar testes
            test_count = content.count('def test_')
            if test_count < 5:
                issues.append(f"Apenas {test_count} testes - cobertura pode ser insuficiente")
        
        elif artifact_type == 'docs':
            # Análise de documentação
            if len(content) < 500:
                issues.append("Documentação muito curta - pode estar incompleta")
            
            if '```' not in content:
                issues.append("Sem exemplos de código - dificulta entendimento")
            
            if 'install' not in content.lower():
                issues.append("Sem instruções de instalação")
        
        return issues
    
    def _generate_contextual_challenges(
        self, 
        content: str, 
        artifact_type: str,
        static_issues: List[str]
    ) -> List[str]:
        """Gera desafios contextuais usando LLM."""
        
        # Limitar tamanho do conteúdo para análise
        content_preview = content[:2000] if len(content) > 2000 else content
        
        prompt = f"""Você é um revisor técnico sênior analisando {artifact_type}.

CONTEÚDO A ANALISAR:
```
{content_preview}
```

PROBLEMAS IDENTIFICADOS AUTOMATICAMENTE:
{chr(10).join(f"- {issue}" for issue in static_issues) if static_issues else "Nenhum problema óbvio"}

TAREFA:
Gere 3-5 desafios ESPECÍFICOS e CONTEXTUAIS baseados neste código real.

REGRAS:
1. Desafios devem ser ESPECÍFICOS ao código mostrado (não genéricos)
2. Cite trechos específicos do código quando relevante
3. Foque em melhorias práticas e mensuráveis
4. Seja direto e construtivo
5. Priorize: segurança, performance, manutenibilidade

FORMATO DE SAÍDA:
Retorne apenas uma lista numerada de desafios, um por linha.
Exemplo:
1. Linha 15: função `create_user` não valida formato de email - adicione regex ou EmailStr do Pydantic
2. Falta tratamento de erro para conexão com banco - adicione try/except com retry logic
3. Endpoint POST não tem rate limiting - vulnerável a abuse

DESAFIOS:"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "Você é um revisor técnico sênior que gera desafios específicos e contextuais."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            challenges_text = response.choices[0].message.content.strip()
            
            # Parse desafios
            challenges = []
            for line in challenges_text.split('\n'):
                line = line.strip()
                # Remover numeração
                if re.match(r'^\d+\.', line):
                    challenge = re.sub(r'^\d+\.\s*', '', line)
                    if challenge:
                        challenges.append(challenge)
            
            print(f"   ✅ {len(challenges)} desafios contextuais gerados")
            
            return challenges
            
        except Exception as e:
            print(f"   ⚠️  Erro ao gerar desafios com LLM: {e}")
            # Fallback: usar apenas análise estática
            return static_issues
    
    def challenge_all_artifacts(self, output_dir: Path) -> Dict[str, List[str]]:
        """
        Gera desafios para todos os artefatos em um diretório.
        
        Returns:
            Dict com {filepath: [challenges]}
        """
        print("\n🎯 GERAÇÃO DE DESAFIOS DINÂMICOS")
        print("=" * 80)
        
        all_challenges = {}
        
        # Mapear extensões para tipos
        type_mapping = {
            '.py': 'code',
            '.md': 'docs',
            '.txt': 'docs',
            '.json': 'config'
        }
        
        # Analisar cada arquivo
        for filepath in output_dir.rglob("*"):
            if filepath.is_file() and filepath.suffix in type_mapping:
                # Determinar tipo
                artifact_type = type_mapping[filepath.suffix]
                
                # Ajustar tipo para testes
                if filepath.name.startswith('test_'):
                    artifact_type = 'tests'
                
                # Gerar desafios
                challenges = self.analyze_and_challenge(filepath, artifact_type)
                
                if challenges:
                    all_challenges[str(filepath)] = challenges
                    
                    print(f"\n📋 Desafios para {filepath.name}:")
                    for i, challenge in enumerate(challenges, 1):
                        print(f"   {i}. {challenge}")
        
        print("\n" + "=" * 80)
        print(f"📊 Total: {len(all_challenges)} arquivos analisados")
        
        return all_challenges
    
    def save_challenges_report(self, challenges: Dict[str, List[str]], output_dir: Path):
        """Salva relatório de desafios."""
        import json
        
        report_path = output_dir / 'CHALLENGES_REPORT.json'
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(challenges, f, indent=2, ensure_ascii=False)
        
        # Também salvar em formato legível
        readable_path = output_dir / 'CHALLENGES.md'
        
        with open(readable_path, 'w', encoding='utf-8') as f:
            f.write("# 🎯 Desafios para Melhoria do Código\n\n")
            f.write("Desafios contextuais gerados automaticamente baseados em análise do código.\n\n")
            f.write("---\n\n")
            
            for filepath, file_challenges in challenges.items():
                filename = Path(filepath).name
                f.write(f"## 📄 {filename}\n\n")
                
                for i, challenge in enumerate(file_challenges, 1):
                    f.write(f"{i}. {challenge}\n")
                
                f.write("\n---\n\n")
        
        print(f"\n📄 Relatórios salvos:")
        print(f"   • {report_path}")
        print(f"   • {readable_path}")


def challenge_code_directory(output_dir: Path) -> Dict[str, List[str]]:
    """
    Gera desafios para código em um diretório.
    
    Args:
        output_dir: Diretório com código gerado
        
    Returns:
        Dict com desafios por arquivo
    """
    challenger = DynamicChallenger()
    challenges = challenger.challenge_all_artifacts(output_dir)
    challenger.save_challenges_report(challenges, output_dir)
    
    return challenges


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python dynamic_challenger.py <diretório>")
        sys.exit(1)
    
    directory = Path(sys.argv[1])
    
    if not directory.exists():
        print(f"❌ Diretório não encontrado: {directory}")
        sys.exit(1)
    
    challenges = challenge_code_directory(directory)
    
    print(f"\n✅ {sum(len(c) for c in challenges.values())} desafios gerados!")

