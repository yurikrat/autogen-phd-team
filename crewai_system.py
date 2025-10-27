#!/usr/bin/env python3
"""
Sistema CrewAI - Agentes que REALMENTE EXECUTAM.
Focado em AÇÃO e ENTREGA, não apenas conversa.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from crewai import Agent, Task, Crew, Process
from crewai_tools import FileWriterTool, DirectoryReadTool

load_dotenv()

# Criar diretório de output
OUTPUT_DIR = Path("./runs") / datetime.now().strftime("%Y%m%d-%H%M%S")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print(f"\n🚀 RUN INICIADA: {OUTPUT_DIR.absolute()}\n")

# Tools para escrever arquivos
file_writer = FileWriterTool(directory=str(OUTPUT_DIR))
dir_reader = DirectoryReadTool(directory=str(OUTPUT_DIR))


def create_code_executor_agent():
    """Agente que CRIA CÓDIGO imediatamente."""
    return Agent(
        role='Code Executor',
        goal='Criar código funcional IMEDIATAMENTE sem pedir mais informações',
        backstory="""Você é um desenvolvedor sênior extremamente proativo.
        
        REGRAS ESTRITAS:
        1. NÃO pergunte nada - EXECUTE imediatamente
        2. Escolha tecnologias padrão (FastAPI, Flask, React)
        3. Crie código COMPLETO e FUNCIONAL
        4. Inclua imports, funções, classes, tudo
        5. Use boas práticas (error handling, validação)
        
        IMPORTANTE: Sua primeira ação DEVE ser criar um arquivo de código.
        Não analise, não planeje - FAÇA!""",
        verbose=True,
        allow_delegation=False,
        tools=[file_writer]
    )


def create_test_writer_agent():
    """Agente que CRIA TESTES imediatamente."""
    return Agent(
        role='Test Writer',
        goal='Criar testes completos para o código criado',
        backstory="""Você é um QA Engineer que escreve testes pytest/jest.
        
        REGRAS:
        1. Leia o código criado
        2. Escreva testes unitários COMPLETOS
        3. Cubra casos de sucesso e erro
        4. Use fixtures e mocks quando necessário
        5. Testes devem ser executáveis
        
        Crie arquivo de teste imediatamente!""",
        verbose=True,
        allow_delegation=False,
        tools=[file_writer, dir_reader]
    )


def create_docs_writer_agent():
    """Agente que CRIA DOCUMENTAÇÃO imediatamente."""
    return Agent(
        role='Documentation Writer',
        goal='Criar documentação clara e completa',
        backstory="""Você é um technical writer que cria docs excelentes.
        
        REGRAS:
        1. Leia o código e testes
        2. Crie README.md com:
           - Descrição do projeto
           - Como instalar
           - Como usar
           - Exemplos de código
           - Como rodar testes
        3. Seja claro e objetivo
        
        Crie documentação imediatamente!""",
        verbose=True,
        allow_delegation=False,
        tools=[file_writer, dir_reader]
    )


def create_tasks(task_description: str, agents: dict):
    """Cria tasks SEQUENCIAIS que forçam execução."""
    
    # Task 1: CRIAR CÓDIGO (obrigatório)
    task_code = Task(
        description=f"""
        TAREFA: {task_description}
        
        AÇÃO IMEDIATA REQUERIDA:
        1. Escolha a tecnologia apropriada (FastAPI para API, React para frontend, etc.)
        2. Crie o arquivo principal com código COMPLETO
        3. Inclua TUDO: imports, funções, classes, error handling, validação
        4. O código deve ser EXECUTÁVEL
        
        IMPORTANTE: Não retorne texto explicativo - retorne o CÓDIGO CRIADO.
        Use file_writer para salvar o arquivo.
        
        Exemplo de nome de arquivo: main.py, app.py, index.js, etc.
        """,
        agent=agents['executor'],
        expected_output="Código completo criado e salvo em arquivo"
    )
    
    # Task 2: CRIAR TESTES (obrigatório)
    task_tests = Task(
        description="""
        AÇÃO IMEDIATA REQUERIDA:
        1. Leia o código criado na task anterior
        2. Crie arquivo de testes (test_*.py ou *.test.js)
        3. Escreva testes unitários COMPLETOS
        4. Cubra casos de sucesso e erro
        5. Use pytest ou jest conforme a linguagem
        
        IMPORTANTE: Não retorne texto - retorne os TESTES CRIADOS.
        Use file_writer para salvar o arquivo de testes.
        """,
        agent=agents['tester'],
        expected_output="Testes completos criados e salvos em arquivo",
        context=[task_code]  # Depende do código
    )
    
    # Task 3: CRIAR DOCS (obrigatório)
    task_docs = Task(
        description="""
        AÇÃO IMEDIATA REQUERIDA:
        1. Leia código e testes criados
        2. Crie README.md completo com:
           - Título e descrição
           - Instalação (requirements/package.json)
           - Como usar (exemplos de código)
           - Como rodar testes
           - Estrutura do projeto
        3. Seja claro e objetivo
        
        IMPORTANTE: Crie o README.md agora.
        Use file_writer para salvar.
        """,
        agent=agents['documenter'],
        expected_output="README.md completo criado e salvo",
        context=[task_code, task_tests]  # Depende de código e testes
    )
    
    return [task_code, task_tests, task_docs]


def run_crew(task_description: str):
    """Executa o crew com a tarefa."""
    
    print("=" * 80)
    print("CRIANDO AGENTES")
    print("=" * 80)
    
    # Criar agentes
    agents = {
        'executor': create_code_executor_agent(),
        'tester': create_test_writer_agent(),
        'documenter': create_docs_writer_agent()
    }
    
    print("\n✅ 3 agentes criados: Code Executor, Test Writer, Documentation Writer\n")
    
    print("=" * 80)
    print("CRIANDO TASKS SEQUENCIAIS")
    print("=" * 80)
    
    # Criar tasks
    tasks = create_tasks(task_description, agents)
    
    print("\n✅ 3 tasks criadas: Código → Testes → Docs\n")
    
    print("=" * 80)
    print("EXECUTANDO CREW")
    print("=" * 80)
    print()
    
    # Criar crew com processo SEQUENCIAL (garante ordem)
    crew = Crew(
        agents=list(agents.values()),
        tasks=tasks,
        process=Process.sequential,  # Executa em ordem
        verbose=True
    )
    
    # EXECUTAR!
    result = crew.kickoff()
    
    print("\n" + "=" * 80)
    print("EXECUÇÃO CONCLUÍDA")
    print("=" * 80)
    
    # Listar arquivos criados
    files = list(OUTPUT_DIR.glob("*"))
    
    print(f"\n📦 Artefatos criados ({len(files)}):")
    for f in files:
        size = f.stat().st_size
        print(f"  ✅ {f.name} ({size} bytes)")
    
    print(f"\n📁 Localização: {OUTPUT_DIR.absolute()}")
    print(f"\n📊 Resultado final:\n{result}\n")
    
    return result, OUTPUT_DIR


def main():
    """Função principal."""
    
    if len(sys.argv) < 2:
        print("❌ ERRO: Task não fornecida.")
        print("   Uso: python crewai_system.py \"Sua tarefa aqui...\"")
        sys.exit(1)
    
    task_description = " ".join(sys.argv[1:])
    
    print("\n" + "=" * 80)
    print("🎼 CREWAI SYSTEM - AGENTES QUE EXECUTAM")
    print("=" * 80)
    print(f"\n📋 TAREFA: {task_description}\n")
    
    try:
        result, output_dir = run_crew(task_description)
        
        print("\n" + "=" * 80)
        print("✅ SUCESSO - ARTEFATOS CRIADOS")
        print("=" * 80)
        print(f"\n📂 Veja os arquivos em: {output_dir.absolute()}\n")
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

