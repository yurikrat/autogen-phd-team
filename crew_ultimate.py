#!/usr/bin/env python3
"""
Crew Ultimate - Sistema completo com 33 agentes especializados.

Funcionalidades:
- 33 agentes organizados por categoria
- Seleção dinâmica baseada em palavras-chave
- Rate limiting para evitar timeout
- Núcleo sempre presente (4 agentes)
- Artefatos organizados por agente

Uso:
    python crew_ultimate.py "Criar API REST com FastAPI usando JWT"
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Adicionar path para imports
sys.path.insert(0, str(Path(__file__).parent))

from crewai import Agent, Task, Crew, Process
from crewai.tools import tool

# Imports locais
from agents.dynamic_selector import (
    get_selected_agents_instances,
    print_selection_summary
)
from utils.rate_limiter import get_rate_limiter, get_api_monitor

load_dotenv()

# Configurar rate limiter
print("\n🚦 Configurando Rate Limiting...")
RATE_LIMITER = get_rate_limiter(
    calls_per_minute=12,  # Muito conservador
    min_delay_seconds=3.0  # 3s entre chamadas
)

# Diretório de output
OUTPUT_DIR = Path("./runs") / datetime.now().strftime("%Y%m%d-%H%M%S")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Tracking de artefatos
ARTIFACTS_BY_AGENT = {}


@tool("save_artifact")
def save_artifact(agent_name: str, filename: str, content: str) -> str:
    """
    Salva artefato criado por um agente.
    
    Args:
        agent_name: Nome do agente (ex: "Backend_Dev")
        filename: Nome do arquivo
        content: Conteúdo do arquivo
    
    Returns:
        Mensagem de sucesso
    """
    # Criar diretório do agente
    agent_dir = OUTPUT_DIR / agent_name.lower().replace(" ", "_").replace("/", "_")
    agent_dir.mkdir(exist_ok=True)
    
    # Limpar marcadores de código
    if content.startswith("```"):
        lines = content.split('\n')
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        content = '\n'.join(lines)
    
    # Salvar arquivo
    filepath = agent_dir / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Tracking
    if agent_name not in ARTIFACTS_BY_AGENT:
        ARTIFACTS_BY_AGENT[agent_name] = []
    
    ARTIFACTS_BY_AGENT[agent_name].append({
        'filename': filename,
        'path': str(filepath),
        'size': len(content)
    })
    
    return f"✅ Artefato salvo: {filepath} ({len(content)} bytes)"


def create_tasks_for_agents(task_description: str, agents: dict) -> list:
    """
    Cria tasks dinamicamente baseado nos agentes selecionados.
    
    Args:
        task_description: Descrição da task principal
        agents: Dict com agentes selecionados
    
    Returns:
        Lista de Tasks
    """
    tasks = []
    core = agents['core']
    selected = agents['selected']
    
    # 1. AI Orchestrator - Decomposição
    task_orchestrator = Task(
        description=f"""Analise a task e decomponha em subtasks:

TASK: {task_description}

Seu trabalho:
1. Identificar componentes principais
2. Definir dependências
3. Criar plano de execução
4. Identificar riscos

Salve: PLAN.md (plano detalhado)""",
        agent=core['AI_Orchestrator'],
        expected_output="Plano de execução detalhado"
    )
    tasks.append(task_orchestrator)
    
    # 2. Project Manager - Roadmap
    task_pm = Task(
        description=f"""Crie roadmap do projeto:

TASK: {task_description}

Crie:
1. ROADMAP.md (milestones, entregas, timeline)

Use save_artifact.""",
        agent=core['Project_Manager'],
        expected_output="Roadmap completo",
        context=[task_orchestrator]
    )
    tasks.append(task_pm)
    
    # 3. Tech Architect - Arquitetura
    task_arch = Task(
        description=f"""Defina arquitetura técnica:

TASK: {task_description}

Crie:
1. ARCHITECTURE.md (tecnologias, padrões, estrutura)
2. DIAGRAM.md (diagrama Mermaid)

Use save_artifact.""",
        agent=core['Tech_Architect'],
        expected_output="Documentação de arquitetura",
        context=[task_orchestrator]
    )
    tasks.append(task_arch)
    
    # 4. Agentes selecionados dinamicamente
    previous_tasks = [task_orchestrator, task_pm, task_arch]
    
    # Backend_Dev
    if 'Backend_Dev' in selected:
        task_backend = Task(
            description=f"""Implemente código backend:

TASK: {task_description}

Baseie-se na arquitetura do Tech_Architect.

Crie:
1. main.py ou app.py
2. models.py (se necessário)
3. requirements.txt

Use save_artifact para cada arquivo.""",
            agent=selected['Backend_Dev'],
            expected_output="Código backend completo",
            context=previous_tasks
        )
        tasks.append(task_backend)
        previous_tasks.append(task_backend)
    
    # Frontend_Dev
    if 'Frontend_Dev' in selected:
        task_frontend = Task(
            description=f"""Implemente interface frontend:

TASK: {task_description}

Crie:
1. App.jsx ou index.html
2. components/ (componentes principais)
3. package.json

Use save_artifact.""",
            agent=selected['Frontend_Dev'],
            expected_output="Código frontend completo",
            context=previous_tasks
        )
        tasks.append(task_frontend)
        previous_tasks.append(task_frontend)
    
    # IAM_Engineer
    if 'IAM_Engineer' in selected:
        task_iam = Task(
            description=f"""Implemente autenticação/autorização:

TASK: {task_description}

Crie:
1. auth.py (lógica de autenticação)
2. AUTH_GUIDE.md (documentação)

Use save_artifact.""",
            agent=selected['IAM_Engineer'],
            expected_output="Sistema de autenticação completo",
            context=previous_tasks
        )
        tasks.append(task_iam)
        previous_tasks.append(task_iam)
    
    # DBA_Engineer
    if 'DBA_Engineer' in selected:
        task_dba = Task(
            description=f"""Projete schema de banco de dados:

TASK: {task_description}

Crie:
1. schema.sql
2. migrations/ (se necessário)
3. DB_GUIDE.md

Use save_artifact.""",
            agent=selected['DBA_Engineer'],
            expected_output="Schema e migrations",
            context=previous_tasks
        )
        tasks.append(task_dba)
        previous_tasks.append(task_dba)
    
    # DevOps_SRE
    if 'DevOps_SRE' in selected:
        task_devops = Task(
            description=f"""Configure CI/CD e containers:

TASK: {task_description}

Crie:
1. Dockerfile
2. docker-compose.yml
3. .github/workflows/ci.yml

Use save_artifact.""",
            agent=selected['DevOps_SRE'],
            expected_output="Configurações de CI/CD",
            context=previous_tasks
        )
        tasks.append(task_devops)
        previous_tasks.append(task_devops)
    
    # QA_Engineer (sempre presente)
    task_qa = Task(
        description=f"""Crie testes completos:

TASK: {task_description}

Crie:
1. test_main.py (pytest)
2. conftest.py (fixtures)

Mínimo 5 testes. Use save_artifact.""",
        agent=selected['QA_Engineer'],
        expected_output="Testes completos",
        context=previous_tasks
    )
    tasks.append(task_qa)
    previous_tasks.append(task_qa)
    
    # Code_Validator (sempre presente)
    task_validator = Task(
        description=f"""Valide todo o código gerado:

Verifique:
1. Imports existem
2. Dependências no requirements.txt
3. Sintaxe correta
4. Código executável

Crie:
1. VALIDATION_REPORT.md

Use save_artifact.""",
        agent=selected['Code_Validator'],
        expected_output="Relatório de validação",
        context=previous_tasks
    )
    tasks.append(task_validator)
    previous_tasks.append(task_validator)
    
    # 5. Finalizer - Consolidação
    task_finalizer = Task(
        description=f"""Consolide entrega final:

Crie:
1. MANIFEST.md (índice de todos os artefatos)
2. README.md (guia completo)
3. CHECKLIST.md (checklist de entrega)

Use save_artifact.""",
        agent=core['Finalizer'],
        expected_output="Documentação final consolidada",
        context=previous_tasks
    )
    tasks.append(task_finalizer)
    
    return tasks


def run_crew_ultimate(task_description: str):
    """Executa crew ultimate com seleção dinâmica."""
    
    print("\n" + "=" * 80)
    print("🚀 CREW ULTIMATE - 33 AGENTES COM SELEÇÃO DINÂMICA")
    print("=" * 80)
    print(f"\n📋 Task: {task_description}")
    print(f"📁 Output: {OUTPUT_DIR.absolute()}\n")
    print("=" * 80)
    
    start_time = time.time()
    
    try:
        # Seleção dinâmica de agentes
        print_selection_summary(task_description)
        
        agents_data = get_selected_agents_instances(task_description)
        
        # Criar tasks
        print("📋 Criando tasks dinamicamente...\n")
        tasks = create_tasks_for_agents(task_description, agents_data)
        
        print(f"✅ {len(tasks)} tasks criadas\n")
        print("=" * 80 + "\n")
        
        # Criar crew
        all_agents = list(agents_data['core'].values()) + list(agents_data['selected'].values())
        
        # Adicionar tool save_artifact a todos os agentes
        for agent in all_agents:
            if save_artifact not in agent.tools:
                agent.tools.append(save_artifact)
        
        print(f"🎼 Iniciando execução com {len(all_agents)} agentes...\n")
        print("⏳ Executando (com rate limiting de 3s entre chamadas)...\n")
        print("=" * 80 + "\n")
        
        crew = Crew(
            agents=all_agents,
            tasks=tasks,
            process=Process.sequential,
            verbose=True
        )
        
        # Executar
        result = crew.kickoff()
        
        print("\n" + "=" * 80)
        print("✅ EXECUÇÃO CONCLUÍDA")
        print("=" * 80 + "\n")
        
        # Estatísticas
        execution_time = time.time() - start_time
        total_artifacts = sum(len(artifacts) for artifacts in ARTIFACTS_BY_AGENT.items())
        
        print(f"⏱️  Tempo total: {execution_time:.1f}s ({execution_time/60:.1f} minutos)")
        print(f"📦 Artefatos criados: {total_artifacts}")
        print(f"📁 Localização: {OUTPUT_DIR.absolute()}\n")
        
        # Listar artefatos por agente
        print("📄 Artefatos por agente:")
        for agent_name, artifacts in sorted(ARTIFACTS_BY_AGENT.items()):
            print(f"\n   {agent_name}:")
            for artifact in artifacts:
                print(f"      • {artifact['filename']} ({artifact['size']} bytes)")
        
        # Estatísticas da API
        monitor = get_api_monitor()
        monitor.print_summary()
        
        # Estatísticas do rate limiter
        limiter_stats = RATE_LIMITER.get_stats()
        print(f"\n🚦 Rate Limiter:")
        print(f"   Chamadas no último minuto: {limiter_stats['calls_last_minute']}")
        print(f"   Utilização: {limiter_stats['utilization_percent']:.1f}%")
        
        print("\n" + "=" * 80)
        print("🎉 CREW ULTIMATE CONCLUÍDO!")
        print("=" * 80 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        
        # Estatísticas mesmo em erro
        monitor = get_api_monitor()
        monitor.print_summary()
        
        return False


def main():
    if len(sys.argv) < 2:
        print("❌ Uso: python crew_ultimate.py \"Sua tarefa...\"")
        print("\nExemplos:")
        print('  python crew_ultimate.py "Criar API REST com FastAPI usando JWT"')
        print('  python crew_ultimate.py "Dashboard analytics com React"')
        print('  python crew_ultimate.py "Pipeline ETL com Airflow"')
        sys.exit(1)
    
    task_description = " ".join(sys.argv[1:])
    
    try:
        success = run_crew_ultimate(task_description)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Execução interrompida pelo usuário")
        
        # Estatísticas
        monitor = get_api_monitor()
        monitor.print_summary()
        
        sys.exit(1)


if __name__ == "__main__":
    main()

