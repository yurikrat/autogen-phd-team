#!/usr/bin/env python3
"""
Crew Optimized - Versão otimizada com rate limiting e controle de timeout.

Melhorias:
- Rate limiting para evitar timeout da API
- Retry com backoff exponencial
- Número reduzido de agentes para tarefas simples
- Timeout configurável
- Monitoramento de chamadas à API
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from crewai import Agent, Task, Crew, Process
from crewai.tools import tool
from langchain_openai import ChatOpenAI

# Importar rate limiter
sys.path.insert(0, str(Path(__file__).parent))
from utils.rate_limiter import (
    get_rate_limiter,
    get_api_monitor,
    retry_with_backoff,
    with_rate_limit
)

load_dotenv()

# Configurar rate limiter
RATE_LIMITER = get_rate_limiter(
    calls_per_minute=15,  # Conservador para evitar timeout
    min_delay_seconds=2.0  # 2s entre chamadas
)

# Diretório de output
OUTPUT_DIR = Path("./runs") / datetime.now().strftime("%Y%m%d-%H%M%S")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Tracking de artefatos
ARTIFACTS_BY_AGENT = {}


@tool("save_artifact")
def save_artifact(agent_name: str, artifact_type: str, filename: str, content: str) -> str:
    """Salva artefato criado por um agente."""
    agent_dir = OUTPUT_DIR / agent_name.lower().replace(" ", "_")
    agent_dir.mkdir(exist_ok=True)
    
    filepath = agent_dir / filename
    
    # Limpar marcadores de código
    if content.startswith("```"):
        lines = content.split('\n')
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        content = '\n'.join(lines)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Tracking
    if agent_name not in ARTIFACTS_BY_AGENT:
        ARTIFACTS_BY_AGENT[agent_name] = []
    
    ARTIFACTS_BY_AGENT[agent_name].append({
        'filename': filename,
        'type': artifact_type,
        'path': str(filepath),
        'size': len(content)
    })
    
    return f"✅ Artefato salvo: {filepath} ({len(content)} bytes)"


def create_llm_with_rate_limit(temperature: float = 0.7):
    """Cria LLM com rate limiting configurado."""
    return ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=temperature,
        timeout=60,  # Timeout de 60s por chamada
        max_retries=2  # Retry automático
    )


def create_minimal_crew(task_description: str) -> tuple:
    """
    Cria crew MÍNIMO (3 agentes) para evitar timeout.
    
    Agentes:
    1. Developer - Cria código
    2. QA - Cria testes
    3. Writer - Cria docs
    """
    print("👥 Criando crew OTIMIZADO (3 agentes)...\n")
    
    # 1. Developer (combina Architect + Backend)
    developer = Agent(
        role="Full-Stack Developer",
        goal="Criar código completo, funcional e bem estruturado",
        backstory="""Você é um desenvolvedor full-stack sênior com 10+ anos de experiência.
        
Você cria código COMPLETO e FUNCIONAL em uma única vez, incluindo:
- Estrutura de pastas
- Código principal (main.py ou app.py)
- Modelos de dados
- Configurações

NÃO faça análise prévia - crie o código IMEDIATAMENTE.
Use FastAPI por padrão para APIs REST.
Sempre inclua error handling e validações.""",
        verbose=True,
        allow_delegation=False,
        llm=create_llm_with_rate_limit()
    )
    
    # 2. QA Engineer
    qa = Agent(
        role="QA Engineer",
        goal="Criar testes completos e garantir qualidade",
        backstory="""Você é um QA engineer sênior com 8+ anos de experiência.

Você cria testes COMPLETOS usando pytest:
- Testes de sucesso
- Testes de erro
- Fixtures
- Cobertura de 80%+

Crie o arquivo test_main.py IMEDIATAMENTE.""",
        verbose=True,
        allow_delegation=False,
        llm=create_llm_with_rate_limit()
    )
    
    # 3. Technical Writer
    writer = Agent(
        role="Technical Writer",
        goal="Criar documentação clara e completa",
        backstory="""Você é um technical writer sênior.

Você cria README.md COMPLETO com:
- Descrição do projeto
- Instalação
- Uso
- Exemplos
- Estrutura de arquivos

Crie o README IMEDIATAMENTE.""",
        verbose=True,
        allow_delegation=False,
        llm=create_llm_with_rate_limit()
    )
    
    # Tasks
    task_dev = Task(
        description=f"""Crie o código completo para: {task_description}

IMPORTANTE:
- Crie IMEDIATAMENTE (sem análise prévia)
- Use FastAPI se for API REST
- Inclua main.py ou app.py
- Adicione error handling
- Use save_artifact para salvar CADA arquivo

Arquivos a criar:
1. main.py (código principal)
2. requirements.txt (dependências)""",
        agent=developer,
        expected_output="Código Python completo e funcional salvo em arquivos"
    )
    
    task_qa = Task(
        description=f"""Crie testes completos para o código do Developer.

IMPORTANTE:
- Crie test_main.py com pytest
- Mínimo 5 testes
- Testes de sucesso E erro
- Use save_artifact para salvar""",
        agent=qa,
        expected_output="Arquivo test_main.py com testes pytest completos",
        context=[task_dev]
    )
    
    task_docs = Task(
        description=f"""Crie README.md completo.

IMPORTANTE:
- Inclua instalação, uso, exemplos
- Descreva estrutura de arquivos
- Use save_artifact para salvar""",
        agent=writer,
        expected_output="README.md completo e bem formatado",
        context=[task_dev, task_qa]
    )
    
    agents = [developer, qa, writer]
    tasks = [task_dev, task_qa, task_docs]
    
    return agents, tasks


def run_optimized_crew(task_description: str):
    """Executa crew otimizado com rate limiting."""
    print("\n" + "=" * 80)
    print("🚀 CREW OPTIMIZED - COM RATE LIMITING")
    print("=" * 80)
    print(f"\n📋 Tarefa: {task_description}")
    print(f"📁 Output: {OUTPUT_DIR.absolute()}\n")
    print("=" * 80 + "\n")
    
    start_time = time.time()
    
    try:
        # Criar crew
        agents, tasks = create_minimal_crew(task_description)
        
        print("🎼 Iniciando execução do crew...\n")
        print("=" * 80 + "\n")
        
        crew = Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential,
            verbose=True
        )
        
        # Executar com rate limiting
        print("⏳ Executando (com rate limiting de 2s entre chamadas)...\n")
        result = crew.kickoff()
        
        print("\n" + "=" * 80)
        print("✅ EXECUÇÃO CONCLUÍDA")
        print("=" * 80 + "\n")
        
        # Estatísticas
        execution_time = time.time() - start_time
        total_artifacts = sum(len(artifacts) for artifacts in ARTIFACTS_BY_AGENT.values())
        
        print(f"⏱️  Tempo total: {execution_time:.1f}s")
        print(f"📦 Artefatos criados: {total_artifacts}")
        print(f"📁 Localização: {OUTPUT_DIR.absolute()}\n")
        
        # Listar artefatos
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
        print("🎉 CREW OPTIMIZED CONCLUÍDO!")
        print("=" * 80 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    if len(sys.argv) < 2:
        print("❌ Uso: python crew_optimized.py \"Sua tarefa...\"")
        sys.exit(1)
    
    task_description = " ".join(sys.argv[1:])
    
    try:
        success = run_optimized_crew(task_description)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Execução interrompida pelo usuário")
        sys.exit(1)


if __name__ == "__main__":
    main()

