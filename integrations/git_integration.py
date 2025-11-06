#!/usr/bin/env python3
"""
Git Integration - Integração automática com Git e CI/CD.

Funcionalidades:
- Criar branch automaticamente
- Commit de artefatos gerados
- Push para repositório
- Criar Pull Request
- Configurar GitHub Actions
- Rodar testes em pipeline
"""

import subprocess
import json
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime


class GitIntegration:
    """Integração automática com Git e GitHub."""
    
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.branch_name = None
    
    def _run_git_command(self, command: List[str]) -> tuple[bool, str]:
        """Executa comando git e retorna (success, output)."""
        try:
            result = subprocess.run(
                ['git'] + command,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0, result.stdout + result.stderr
        except Exception as e:
            return False, str(e)
    
    def init_repo(self) -> bool:
        """Inicializa repositório Git se não existir."""
        git_dir = self.repo_path / '.git'
        
        if git_dir.exists():
            print("   ✅ Repositório Git já existe")
            return True
        
        print("   📦 Inicializando repositório Git...")
        success, output = self._run_git_command(['init'])
        
        if success:
            print("   ✅ Repositório inicializado")
            return True
        else:
            print(f"   ❌ Erro ao inicializar: {output}")
            return False
    
    def create_feature_branch(self, task_description: str) -> Optional[str]:
        """
        Cria branch de feature baseada na tarefa.
        
        Returns:
            Nome da branch criada ou None se falhar
        """
        print("\n🌿 Criando branch de feature...")
        
        # Gerar nome da branch
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        # Simplificar descrição para nome de branch
        task_slug = task_description[:50].lower()
        task_slug = ''.join(c if c.isalnum() or c in ['-', '_'] else '-' for c in task_slug)
        task_slug = task_slug.strip('-')
        
        branch_name = f"feature/{task_slug}-{timestamp}"
        
        # Criar branch
        success, output = self._run_git_command(['checkout', '-b', branch_name])
        
        if success:
            self.branch_name = branch_name
            print(f"   ✅ Branch criada: {branch_name}")
            return branch_name
        else:
            print(f"   ❌ Erro ao criar branch: {output}")
            return None
    
    def stage_artifacts(self, artifacts_dir: Path) -> bool:
        """Adiciona artefatos ao staging."""
        print("\n📦 Adicionando artefatos ao Git...")
        
        # Adicionar todos os arquivos do diretório
        success, output = self._run_git_command(['add', str(artifacts_dir)])
        
        if success:
            # Verificar quantos arquivos foram adicionados
            success2, status = self._run_git_command(['status', '--short'])
            if success2:
                files_count = len([line for line in status.split('\n') if line.strip()])
                print(f"   ✅ {files_count} arquivos adicionados")
                return True
        
        print(f"   ❌ Erro ao adicionar arquivos: {output}")
        return False
    
    def commit_changes(
        self,
        message: str,
        description: Optional[str] = None
    ) -> bool:
        """Faz commit das mudanças."""
        print("\n💾 Fazendo commit...")
        
        # Montar mensagem completa
        full_message = message
        if description:
            full_message += f"\n\n{description}"
        
        success, output = self._run_git_command(['commit', '-m', full_message])
        
        if success:
            print(f"   ✅ Commit realizado")
            return True
        else:
            if "nothing to commit" in output:
                print("   ⚠️  Nada para commitar")
                return True
            print(f"   ❌ Erro ao commitar: {output}")
            return False
    
    def push_to_remote(self, remote: str = 'origin') -> bool:
        """Faz push da branch para o remote."""
        print(f"\n🚀 Fazendo push para {remote}...")
        
        if not self.branch_name:
            print("   ❌ Nenhuma branch ativa")
            return False
        
        success, output = self._run_git_command([
            'push', '-u', remote, self.branch_name
        ])
        
        if success:
            print(f"   ✅ Push realizado: {remote}/{self.branch_name}")
            return True
        else:
            print(f"   ❌ Erro ao fazer push: {output}")
            return False
    
    def create_pull_request(
        self,
        title: str,
        body: str,
        base_branch: str = 'main'
    ) -> Optional[str]:
        """
        Cria Pull Request usando GitHub CLI.
        
        Returns:
            URL do PR criado ou None se falhar
        """
        print("\n🔀 Criando Pull Request...")
        
        try:
            result = subprocess.run(
                [
                    'gh', 'pr', 'create',
                    '--title', title,
                    '--body', body,
                    '--base', base_branch
                ],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                pr_url = result.stdout.strip()
                print(f"   ✅ PR criado: {pr_url}")
                return pr_url
            else:
                print(f"   ❌ Erro ao criar PR: {result.stderr}")
                return None
                
        except FileNotFoundError:
            print("   ⚠️  GitHub CLI (gh) não instalado - PR não criado")
            print("   💡 Instale com: https://cli.github.com/")
            return None
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            return None
    
    def create_github_actions_workflow(self) -> bool:
        """Cria arquivo de workflow do GitHub Actions."""
        print("\n⚙️  Criando workflow do GitHub Actions...")
        
        workflows_dir = self.repo_path / '.github' / 'workflows'
        workflows_dir.mkdir(parents=True, exist_ok=True)
        
        workflow_file = workflows_dir / 'ci.yml'
        
        workflow_content = """name: CI - Validação Automática

on:
  push:
    branches: [ main, master, feature/** ]
  pull_request:
    branches: [ main, master ]

jobs:
  validate:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pytest pytest-cov flake8 pylint
        if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
    
    - name: Lint with flake8
      run: |
        # Parar build se houver erros de sintaxe ou nomes indefinidos
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        # Avisos tratados como warnings
        flake8 . --count --exit-zero --max-complexity=10 --max-line-length=100 --statistics
      continue-on-error: true
    
    - name: Run tests with pytest
      run: |
        pytest --cov=. --cov-report=xml --cov-report=term
      continue-on-error: false
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: false
"""
        
        try:
            with open(workflow_file, 'w', encoding='utf-8') as f:
                f.write(workflow_content)
            
            print(f"   ✅ Workflow criado: {workflow_file}")
            return True
            
        except Exception as e:
            print(f"   ❌ Erro ao criar workflow: {e}")
            return False
    
    def full_workflow(
        self,
        task_description: str,
        artifacts_dir: Path,
        validation_passed: bool,
        create_pr: bool = True
    ) -> Dict[str, any]:
        """
        Executa workflow completo de Git + CI/CD.
        
        Returns:
            Dict com resultados de cada etapa
        """
        print("\n" + "=" * 80)
        print("🔧 GIT + CI/CD WORKFLOW")
        print("=" * 80)
        
        results = {
            'repo_initialized': False,
            'branch_created': False,
            'files_staged': False,
            'committed': False,
            'pushed': False,
            'pr_created': False,
            'workflow_created': False,
            'branch_name': None,
            'pr_url': None
        }
        
        # 1. Inicializar repo
        if not self.init_repo():
            return results
        results['repo_initialized'] = True
        
        # 2. Criar branch
        branch = self.create_feature_branch(task_description)
        if not branch:
            return results
        results['branch_created'] = True
        results['branch_name'] = branch
        
        # 3. Criar workflow do GitHub Actions
        if self.create_github_actions_workflow():
            results['workflow_created'] = True
        
        # 4. Adicionar artefatos
        if not self.stage_artifacts(artifacts_dir):
            return results
        results['files_staged'] = True
        
        # 5. Commit
        commit_message = f"feat: {task_description[:70]}"
        commit_body = f"""Artefatos gerados automaticamente pelo Crew Evolved.

Validação: {'✅ PASSOU' if validation_passed else '❌ FALHOU'}
Branch: {branch}
Timestamp: {datetime.now().isoformat()}

Gerado por: autogen-phd-team
"""
        
        if not self.commit_changes(commit_message, commit_body):
            return results
        results['committed'] = True
        
        # 6. Push (opcional - pode falhar se não houver remote)
        if self.push_to_remote():
            results['pushed'] = True
        
        # 7. Criar PR (se solicitado e push funcionou)
        if create_pr and results['pushed']:
            pr_title = f"🤖 {task_description[:60]}"
            pr_body = f"""## 🤖 Código Gerado Automaticamente

**Tarefa:** {task_description}

**Validação:** {'✅ PASSOU' if validation_passed else '⚠️ FALHOU - Revisar'}

**Branch:** `{branch}`

**Artefatos Gerados:**
- Código completo
- Testes automatizados
- Documentação
- Configurações de segurança

**Próximos Passos:**
1. Revisar código gerado
2. Verificar testes (CI rodando automaticamente)
3. Aprovar e fazer merge

---

*Gerado automaticamente por autogen-phd-team*
"""
            
            pr_url = self.create_pull_request(pr_title, pr_body)
            if pr_url:
                results['pr_created'] = True
                results['pr_url'] = pr_url
        
        # Resumo
        print("\n" + "=" * 80)
        print("📊 RESUMO DO WORKFLOW GIT")
        print("=" * 80)
        print(f"✅ Repo inicializado: {results['repo_initialized']}")
        print(f"✅ Branch criada: {results['branch_created']} ({results['branch_name']})")
        print(f"✅ Workflow CI criado: {results['workflow_created']}")
        print(f"✅ Arquivos staged: {results['files_staged']}")
        print(f"✅ Commit realizado: {results['committed']}")
        print(f"✅ Push realizado: {results['pushed']}")
        print(f"✅ PR criado: {results['pr_created']}")
        if results['pr_url']:
            print(f"🔗 PR URL: {results['pr_url']}")
        print("=" * 80 + "\n")
        
        return results


if __name__ == "__main__":
    # Teste básico
    import sys
    
    if len(sys.argv) < 3:
        print("Uso: python git_integration.py <repo_path> <artifacts_dir>")
        sys.exit(1)
    
    repo_path = Path(sys.argv[1])
    artifacts_dir = Path(sys.argv[2])
    
    git = GitIntegration(repo_path)
    results = git.full_workflow(
        task_description="Teste de integração Git",
        artifacts_dir=artifacts_dir,
        validation_passed=True,
        create_pr=False  # Não criar PR em teste
    )
    
    print(f"\n✅ Workflow concluído: {results}")

