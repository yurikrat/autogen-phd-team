#!/usr/bin/env python3
"""
Crew With Rate Limit - Wrapper do crew_advanced.py com rate limiting.

Mantém TODOS os 5 agentes especializados:
1. Software Architect
2. Backend Developer
3. QA Engineer
4. Security Expert
5. Technical Writer

Adiciona apenas:
- Rate limiting (2s entre chamadas)
- Timeout configurável
- Monitoramento de API
- Retry automático
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Importar do crew_advanced original
sys.path.insert(0, str(Path(__file__).parent))
from crew_advanced import (
    OUTPUT_DIR,
    ARTIFACTS_BY_AGENT,
    save_artifact
)

from crewai import Agent, Task, Crew, Process
from crewai.tools import tool
from langchain_openai import ChatOpenAI

# Importar rate limiter
from utils.rate_limiter import get_rate_limiter, get_api_monitor

load_dotenv()

# Configurar rate limiter
print("\n🚦 Configurando Rate Limiting...")
RATE_LIMITER = get_rate_limiter(
    calls_per_minute=15,  # Conservador
    min_delay_seconds=2.5  # 2.5s entre chamadas
)


def create_llm_with_rate_limit(temperature=0.7):
    """Cria LLM com timeout e retry configurados."""
    return ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=temperature,
        timeout=120,  # 2 minutos por chamada
        max_retries=3,  # Retry automático
        request_timeout=120
    )


def create_architect_agent():
    """Arquiteto de Software."""
    return Agent(
        role='Software Architect',
        goal='Definir arquitetura robusta, escalável e com boas práticas',
        backstory="""Você é um arquiteto de software sênior com 15+ anos de experiência.

Expertise: Padrões de design, arquitetura limpa, microserviços, APIs RESTful.

Seu trabalho:
1. Analisar requisitos
2. Definir arquitetura (diagrama, estrutura)
3. Escolher tecnologias
4. Criar documento ARCHITECTURE.md

Seja decisivo e pragmático. Use tecnologias modernas.""",
        verbose=True,
        allow_delegation=False,
        tools=[save_artifact],
        llm=create_llm_with_rate_limit()
    )


def create_backend_dev_agent():
    """Desenvolvedor Backend."""
    return Agent(
        role='Backend Developer',
        goal='Implementar código backend robusto e testável',
        backstory="""Você é um desenvolvedor backend expert em Python/FastAPI.

Expertise: FastAPI, APIs RESTful, Pydantic, error handling, async/await.

Seu trabalho:
1. Implementar endpoints da API
2. Criar modelos e validações
3. Implementar lógica de negócio
4. Error handling robusto

Código deve ser limpo, testável e bem documentado.""",
        verbose=True,
        allow_delegation=False,
        tools=[save_artifact],
        llm=create_llm_with_rate_limit()
    )


def create_qa_engineer_agent():
    """Engenheiro de QA."""
    return Agent(
        role='QA Engineer',
        goal='Criar testes completos e garantir qualidade',
        backstory="""Você é um QA engineer sênior com 10+ anos de experiência.

Expertise: pytest, testes unitários, integração, fixtures, mocking.

Seu trabalho:
1. Criar test_main.py com pytest
2. Testes de sucesso E erro
3. Fixtures e mocking
4. Cobertura 80%+

Crie testes COMPLETOS e EXECUTÁVEIS.""",
        verbose=True,
        allow_delegation=False,
        tools=[save_artifact],
        llm=create_llm_with_rate_limit()
    )


def create_security_expert_agent():
    """Especialista em Segurança."""
    return Agent(
        role='Security Expert',
        goal='Garantir segurança e proteção contra vulnerabilidades',
        backstory="""Você é um security expert com 12+ anos de experiência.

Expertise: OWASP Top 10, autenticação, autorização, criptografia, rate limiting.

Seu trabalho:
1. Revisar código para vulnerabilidades
2. Implementar validações de segurança
3. Adicionar rate limiting
4. Criar guia de segurança

Seja completo mas conciso.""",
        verbose=True,
        allow_delegation=False,
        tools=[save_artifact],
        llm=create_llm_with_rate_limit()
    )


def create_tech_writer_agent():
    """Technical Writer."""
    return Agent(
        role='Technical Writer',
        goal='Criar documentação clara e completa',
        backstory="""Você é um technical writer sênior com 8+ anos de experiência.

Expertise: Documentação técnica, Markdown, tutoriais, API docs.

Seu trabalho:
1. Criar README.md completo
2. Documentar instalação e uso
3. Adicionar exemplos práticos
4. Estrutura de arquivos

Documente TUDO de forma clara.""",
        verbose=True,
        allow_delegation=False,
        tools=[save_artifact],
        llm=create_llm_with_rate_limit()
    )


def create_tasks(task_description: str, agents: dict):
    """Cria tasks sequenciais para os agentes."""
    
    task_architecture = Task(
        description=f"""Defina a arquitetura para: {task_description}

Crie:
1. ARCHITECTURE.md (estrutura, tecnologias, padrões)
2. DIAGRAM.md (diagrama Mermaid)

Use save_artifact para cada arquivo.""",
        agent=agents['architect'],
        expected_output="Documentos de arquitetura completos"
    )
    
    task_backend = Task(
        description=f"""Implemente o código backend para: {task_description}

Baseie-se na arquitetura do Architect.

Crie:
1. main.py ou app.py (código principal)
2. models.py (se necessário)
3. requirements.txt

Use save_artifact para cada arquivo.""",
        agent=agents['backend'],
        expected_output="Código Python completo e funcional",
        context=[task_architecture]
    )
    
    task_tests = Task(
        description=f"""Crie testes completos para o código do Backend Developer.

Crie:
1. test_main.py (testes pytest)
2. conftest.py (fixtures, se necessário)

Mínimo 5 testes. Use save_artifact.""",
        agent=agents['qa'],
        expected_output="Testes pytest completos",
        context=[task_backend]
    )
    
    task_security = Task(
        description=f"""Revise o código e adicione configurações de segurança.

Crie:
1. security_config.py (configurações)
2. SECURITY.md (guia de segurança)

Use save_artifact.""",
        agent=agents['security'],
        expected_output="Configurações de segurança e documentação",
        context=[task_backend]
    )
    
    task_docs = Task(
        description=f"""Crie documentação completa do projeto.

Crie:
1. README.md (instalação, uso, exemplos)
2. API_GUIDE.md (se for API)

Use save_artifact.""",
        agent=agents['writer'],
        expected_output="Documentação completa",
        context=[task_architecture, task_backend, task_tests]
    )
    
    return [task_architecture, task_backend, task_tests, task_security, task_docs]


def run_crew_with_rate_limit(task_description: str):
    """Executa crew com TODOS os 5 agentes + rate limiting."""
    
    print("\n" + "=" * 80)
    print("🎼 CREW COM RATE LIMITING - 5 AGENTES ESPECIALIZADOS")
    print("=" * 80)
    print(f"\n📋 Tarefa: {task_description}")
    print(f"📁 Output: {OUTPUT_DIR.absolute()}")
    print(f"🚦 Rate Limit: 15 chamadas/min, 2.5s entre chamadas\n")
    print("=" * 80 + "\n")
    
    start_time = time.time()
    
    try:
        # Criar agentes
        print("👥 Criando 5 agentes especializados...\n")
        agents = {
            'architect': create_architect_agent(),
            'backend': create_backend_dev_agent(),
            'qa': create_qa_engineer_agent(),
            'security': create_security_expert_agent(),
            'writer': create_tech_writer_agent()
        }
        
        # Criar tasks
        print("📋 Criando tasks sequenciais...\n")
        tasks = create_tasks(task_description, agents)
        
        # Criar crew
        print("🎼 Iniciando execução do crew...\n")
        print("=" * 80 + "\n")
        
        crew = Crew(
            agents=list(agents.values()),
            tasks=tasks,
            process=Process.sequential,
            verbose=True
        )
        
        # Executar
        print("⏳ Executando (com rate limiting automático)...\n")
        result = crew.kickoff()
        
        print("\n" + "=" * 80)
        print("✅ EXECUÇÃO CONCLUÍDA")
        print("=" * 80 + "\n")
        
        # Estatísticas
        execution_time = time.time() - start_time
        total_artifacts = sum(len(artifacts) for artifacts in ARTIFACTS_BY_AGENT.values())
        
        print(f"⏱️  Tempo total: {execution_time:.1f}s ({execution_time/60:.1f} minutos)")
        print(f"📦 Artefatos criados: {total_artifacts}")
        print(f"📁 Localização: {OUTPUT_DIR.absolute()}\n")
        
        # Listar artefatos por agente
        print("📄 Artefatos por agente:")
        for agent_name, artifacts in ARTIFACTS_BY_AGENT.items():
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
        print("🎉 CREW CONCLUÍDO COM SUCESSO!")
        print("=" * 80 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        
        # Estatísticas mesmo em caso de erro
        monitor = get_api_monitor()
        monitor.print_summary()
        
        return False


def main():
    if len(sys.argv) < 2:
        print("❌ Uso: python crew_with_rate_limit.py \"Sua tarefa...\"")
        sys.exit(1)
    
    task_description = " ".join(sys.argv[1:])
    
    try:
        success = run_crew_with_rate_limit(task_description)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Execução interrompida pelo usuário")
        
        # Estatísticas
        monitor = get_api_monitor()
        monitor.print_summary()
        
        sys.exit(1)


if __name__ == "__main__":
    main()

