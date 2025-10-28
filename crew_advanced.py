#!/usr/bin/env python3
"""
Crew Advanced - Sistema com múltiplos agentes especializados.

Cada agente tem sua expertise e cria seus próprios artefatos.
Colaboração orgânica com desafios e revisões.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from crewai import Agent, Task, Crew, Process
from crewai.tools import tool

load_dotenv()

# Diretório de output
OUTPUT_DIR = Path("./runs") / datetime.now().strftime("%Y%m%d-%H%M%S")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Tracking de artefatos por agente
ARTIFACTS_BY_AGENT = {}


@tool("save_artifact")
def save_artifact(agent_name: str, artifact_type: str, filename: str, content: str) -> str:
    """
    Salva artefato criado por um agente.
    
    Args:
        agent_name: Nome do agente (ex: "Architect", "Backend_Dev")
        artifact_type: Tipo do artefato (ex: "code", "docs", "tests", "diagram")
        filename: Nome do arquivo
        content: Conteúdo do arquivo
    
    Returns:
        Mensagem de sucesso com path do arquivo
    """
    # Criar diretório do agente
    agent_dir = OUTPUT_DIR / agent_name.lower().replace(" ", "_")
    agent_dir.mkdir(exist_ok=True)
    
    # Salvar arquivo
    filepath = agent_dir / filename
    
    # Remover marcadores de código se houver
    if content.startswith('```'):
        lines = content.split('\n')
        if lines[0].startswith('```'):
            lines = lines[1:]
        if lines and lines[-1].strip() == '```':
            lines = lines[:-1]
        content = '\n'.join(lines)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Registrar artefato
    if agent_name not in ARTIFACTS_BY_AGENT:
        ARTIFACTS_BY_AGENT[agent_name] = []
    
    ARTIFACTS_BY_AGENT[agent_name].append({
        'type': artifact_type,
        'filename': filename,
        'path': str(filepath),
        'size': filepath.stat().st_size,
        'timestamp': datetime.now().isoformat()
    })
    
    return f"✅ Artefato salvo: {filepath} ({filepath.stat().st_size} bytes)"


def create_architect_agent():
    """Arquiteto de Software - Define estrutura e padrões."""
    return Agent(
        role='Software Architect',
        goal='Definir arquitetura robusta, escalável e com boas práticas',
        backstory="""Você é um arquiteto de software sênior com 15 anos de experiência.
        
        Expertise:
        - Padrões de design (MVC, Repository, Factory, etc.)
        - Arquitetura limpa e SOLID
        - Microserviços e APIs RESTful
        - Escolha de tecnologias apropriadas
        
        Seu trabalho:
        1. Analisar requisitos
        2. Definir arquitetura (diagrama, estrutura de pastas)
        3. Escolher tecnologias e padrões
        4. Criar documento de arquitetura
        
        Seja decisivo e pragmático. Escolha tecnologias modernas e populares.""",
        verbose=True,
        allow_delegation=False,
        tools=[save_artifact]
    )


def create_backend_dev_agent():
    """Desenvolvedor Backend - Implementa lógica de negócio."""
    return Agent(
        role='Backend Developer',
        goal='Implementar código backend robusto, testável e bem estruturado',
        backstory="""Você é um desenvolvedor backend expert em Python/FastAPI.
        
        Expertise:
        - FastAPI, Flask, Django
        - APIs RESTful
        - Validação com Pydantic
        - Error handling e logging
        - Async/await
        
        Seu trabalho:
        1. Implementar endpoints da API
        2. Criar modelos e validações
        3. Implementar lógica de negócio
        4. Error handling robusto
        5. Documentação inline
        
        Código deve ser COMPLETO, EXECUTÁVEL e seguir boas práticas.""",
        verbose=True,
        allow_delegation=False,
        tools=[save_artifact]
    )


def create_qa_engineer_agent():
    """QA Engineer - Cria testes completos."""
    return Agent(
        role='QA Engineer',
        goal='Criar testes completos que garantam qualidade e cobertura',
        backstory="""Você é um QA Engineer especializado em testes automatizados.
        
        Expertise:
        - Pytest, unittest
        - Test-driven development (TDD)
        - Testes unitários e de integração
        - Fixtures e mocks
        - Cobertura de código
        
        Seu trabalho:
        1. Criar testes unitários completos
        2. Testes de integração
        3. Casos de sucesso e erro
        4. Edge cases
        5. Fixtures reutilizáveis
        
        Testes devem cobrir 80%+ do código.""",
        verbose=True,
        allow_delegation=False,
        tools=[save_artifact]
    )


def create_security_expert_agent():
    """Security Expert - Analisa e melhora segurança."""
    return Agent(
        role='Security Expert',
        goal='Identificar vulnerabilidades e implementar práticas de segurança',
        backstory="""Você é um especialista em segurança de aplicações.
        
        Expertise:
        - OWASP Top 10
        - Autenticação e autorização
        - Validação e sanitização
        - Rate limiting
        - Proteção contra ataques comuns
        
        Seu trabalho:
        1. Revisar código para vulnerabilidades
        2. Implementar validações de segurança
        3. Adicionar rate limiting
        4. Criar guia de segurança
        5. Sugerir melhorias
        
        Seja rigoroso e detalhista.""",
        verbose=True,
        allow_delegation=False,
        tools=[save_artifact]
    )


def create_tech_writer_agent():
    """Technical Writer - Documenta tudo."""
    return Agent(
        role='Technical Writer',
        goal='Criar documentação clara, completa e fácil de seguir',
        backstory="""Você é um technical writer especializado em documentação de APIs.
        
        Expertise:
        - Documentação de APIs
        - READMEs estruturados
        - Guias de instalação
        - Exemplos práticos
        - Diagramas e visualizações
        
        Seu trabalho:
        1. README.md completo
        2. Guia de instalação
        3. Exemplos de uso
        4. Documentação de endpoints
        5. Troubleshooting
        
        Documentação deve ser clara para iniciantes e útil para experts.""",
        verbose=True,
        allow_delegation=False,
        tools=[save_artifact]
    )


def create_tasks(task_description: str, agents: dict):
    """Cria tasks sequenciais com colaboração."""
    
    # Task 1: Arquitetura
    task_architecture = Task(
        description=f"""
        Tarefa: {task_description}
        
        Sua responsabilidade:
        1. Analise os requisitos
        2. Defina a arquitetura (escolha FastAPI/Flask, estrutura de pastas, padrões)
        3. Crie um documento de arquitetura (ARCHITECTURE.md)
        4. Crie um diagrama de componentes (DIAGRAM.md em formato Mermaid)
        
        Use a tool save_artifact para salvar:
        - save_artifact("Architect", "docs", "ARCHITECTURE.md", conteúdo)
        - save_artifact("Architect", "diagram", "DIAGRAM.md", diagrama_mermaid)
        
        Seja específico sobre tecnologias e estrutura.
        """,
        agent=agents['architect'],
        expected_output="Documento de arquitetura e diagrama criados"
    )
    
    # Task 2: Implementação Backend
    task_backend = Task(
        description="""
        Com base na arquitetura definida:
        
        1. Implemente o código principal (main.py ou app.py)
        2. Crie modelos Pydantic
        3. Implemente endpoints completos
        4. Adicione error handling
        5. Crie requirements.txt
        
        Use save_artifact para cada arquivo:
        - save_artifact("Backend_Dev", "code", "main.py", código)
        - save_artifact("Backend_Dev", "code", "models.py", modelos)
        - save_artifact("Backend_Dev", "config", "requirements.txt", deps)
        
        Código deve ser COMPLETO e EXECUTÁVEL.
        """,
        agent=agents['backend'],
        expected_output="Código backend completo implementado",
        context=[task_architecture]
    )
    
    # Task 3: Testes
    task_tests = Task(
        description="""
        Com base no código implementado:
        
        1. Crie testes unitários completos (test_main.py)
        2. Testes de integração se necessário
        3. Fixtures reutilizáveis
        4. Cobertura de casos de sucesso e erro
        5. Edge cases
        
        Use save_artifact:
        - save_artifact("QA_Engineer", "tests", "test_main.py", testes)
        - save_artifact("QA_Engineer", "tests", "conftest.py", fixtures) se necessário
        
        Mínimo 8 testes cobrindo diferentes cenários.
        """,
        agent=agents['qa'],
        expected_output="Testes completos criados",
        context=[task_backend]
    )
    
    # Task 4: Segurança
    task_security = Task(
        description="""
        Revise o código e implemente melhorias de segurança:
        
        1. Analise vulnerabilidades
        2. Crie arquivo de configuração de segurança (security_config.py)
        3. Adicione validações extras se necessário
        4. Crie guia de segurança (SECURITY.md)
        
        Use save_artifact:
        - save_artifact("Security_Expert", "code", "security_config.py", config)
        - save_artifact("Security_Expert", "docs", "SECURITY.md", guia)
        
        Seja rigoroso e detalhado.
        """,
        agent=agents['security'],
        expected_output="Análise de segurança e melhorias implementadas",
        context=[task_backend]
    )
    
    # Task 5: Documentação
    task_docs = Task(
        description="""
        Crie documentação completa do projeto:
        
        1. README.md principal
        2. Guia de instalação
        3. Exemplos de uso
        4. Documentação de API
        5. Troubleshooting
        
        Use save_artifact:
        - save_artifact("Tech_Writer", "docs", "README.md", readme)
        - save_artifact("Tech_Writer", "docs", "API_GUIDE.md", api_docs)
        
        Documentação deve ser clara e completa.
        """,
        agent=agents['writer'],
        expected_output="Documentação completa criada",
        context=[task_architecture, task_backend, task_tests, task_security]
    )
    
    return [task_architecture, task_backend, task_tests, task_security, task_docs]


def generate_summary():
    """Gera resumo dos artefatos criados."""
    
    summary = {
        'timestamp': datetime.now().isoformat(),
        'output_dir': str(OUTPUT_DIR),
        'agents': {},
        'total_artifacts': 0,
        'total_size': 0
    }
    
    for agent_name, artifacts in ARTIFACTS_BY_AGENT.items():
        agent_summary = {
            'artifacts_count': len(artifacts),
            'artifacts': artifacts,
            'total_size': sum(a['size'] for a in artifacts)
        }
        summary['agents'][agent_name] = agent_summary
        summary['total_artifacts'] += len(artifacts)
        summary['total_size'] += agent_summary['total_size']
    
    # Salvar summary
    summary_path = OUTPUT_DIR / 'SUMMARY.json'
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    return summary


def main():
    if len(sys.argv) < 2:
        print("❌ Uso: python crew_advanced.py \"Sua tarefa...\"")
        sys.exit(1)
    
    task_description = " ".join(sys.argv[1:])
    
    print("\n" + "=" * 80)
    print("🎼 CREW ADVANCED - AGENTES ESPECIALIZADOS")
    print("=" * 80)
    print(f"\n📋 Tarefa: {task_description}")
    print(f"📁 Output: {OUTPUT_DIR.absolute()}\n")
    print("=" * 80 + "\n")
    
    try:
        # Criar agentes
        print("👥 Criando agentes especializados...\n")
        agents = {
            'architect': create_architect_agent(),
            'backend': create_backend_dev_agent(),
            'qa': create_qa_engineer_agent(),
            'security': create_security_expert_agent(),
            'writer': create_tech_writer_agent()
        }
        print("✅ 5 agentes criados: Architect, Backend Dev, QA, Security, Tech Writer\n")
        
        # Criar tasks
        print("📋 Criando tasks sequenciais...\n")
        tasks = create_tasks(task_description, agents)
        print("✅ 5 tasks criadas: Arquitetura → Backend → Testes → Segurança → Docs\n")
        
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
        result = crew.kickoff()
        
        print("\n" + "=" * 80)
        print("✅ EXECUÇÃO CONCLUÍDA")
        print("=" * 80 + "\n")
        
        # Gerar summary
        summary = generate_summary()
        
        # Mostrar resultados
        print(f"📦 Artefatos criados: {summary['total_artifacts']}")
        print(f"💾 Tamanho total: {summary['total_size']} bytes\n")
        
        print("📂 Por agente:")
        for agent_name, agent_data in summary['agents'].items():
            print(f"\n  👤 {agent_name}:")
            print(f"     Artefatos: {agent_data['artifacts_count']}")
            for artifact in agent_data['artifacts']:
                print(f"     • {artifact['filename']} ({artifact['size']} bytes) - {artifact['type']}")
        
        print(f"\n📁 Localização: {OUTPUT_DIR.absolute()}")
        print(f"📄 Summary: SUMMARY.json\n")
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

