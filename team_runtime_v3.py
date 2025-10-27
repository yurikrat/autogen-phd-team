#!/usr/bin/env python3
"""
Team Runtime V3: Com iteração manual do stream para debug.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from autogen_ext.models.openai import OpenAIChatCompletionClient

from tools.artifact_store import init_store
from tools import io_tools
from autogen_core.tools import FunctionTool


async def main():
    # Carregar variáveis de ambiente
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ ERRO: OPENAI_API_KEY não encontrada no .env")
        sys.exit(1)
    
    # Verificar se task foi fornecida
    if len(sys.argv) < 2:
        print("❌ ERRO: Task não fornecida.")
        print("   Uso: python team_runtime_v3.py \"Sua tarefa aqui...\"")
        sys.exit(1)
    
    task_text = " ".join(sys.argv[1:])
    
    # Inicializar ArtifactStore
    store = init_store()
    print(f"\n🚀 RUN INICIADA: {store.run_dir.absolute()}\n")
    
    # Criar modelo de linguagem
    model_client = OpenAIChatCompletionClient(
        model="gpt-4.1-mini",
        api_key=api_key,
    )
    
    # Criar FunctionTools das funções de I/O
    tools = [
        FunctionTool(io_tools.report_progress, description="Reporta progresso ao longo da execução"),
        FunctionTool(io_tools.save_text, description="Salva arquivo de texto (.txt)"),
        FunctionTool(io_tools.save_markdown, description="Salva arquivo Markdown (.md)"),
        FunctionTool(io_tools.save_json, description="Salva arquivo JSON. Parâmetros: name (nome do arquivo), data (dicionário Python a ser salvo), relative_path (opcional)"),
        FunctionTool(io_tools.list_artifacts, description="Lista todos os artefatos registrados"),
        FunctionTool(io_tools.finalize_run, description="Finaliza a run gerando MANIFEST.md"),
    ]
    
    # Criar agentes (versão simplificada com apenas 3 agentes)
    orchestrator = AssistantAgent(
        name="Orchestrator",
        model_client=model_client,
        tools=tools,
        system_message="""Você é o Orchestrator. Sua responsabilidade é:
1. Analisar a task e coordenar a execução
2. Usar report_progress para reportar o que está fazendo
3. Delegar para o Developer a implementação
4. Passar para o Finalizer quando tudo estiver pronto

Use report_progress frequentemente!""",
    )
    
    developer = AssistantAgent(
        name="Developer",
        model_client=model_client,
        tools=tools,
        system_message="""Você é o Developer. Sua responsabilidade é:
1. Implementar o que foi solicitado
2. Usar as tools save_* para salvar artefatos (save_json, save_markdown, save_text)
3. Usar report_progress para reportar progresso
4. Confirmar quando terminar

IMPORTANTE: Sempre salve os artefatos usando as tools!""",
    )
    
    finalizer = AssistantAgent(
        name="Finalizer",
        model_client=model_client,
        tools=tools,
        system_message="""Você é o Finalizer. Sua responsabilidade é:
1. Aguardar até que o Developer tenha concluído
2. Chamar list_artifacts() para listar artefatos
3. Chamar finalize_run() para gerar MANIFEST.md
4. Anunciar os caminhos dos artefatos
5. Encerrar com a palavra "CONCLUÍDO" (exatamente assim, em maiúsculas)

Você é o último a falar!""",
    )
    
    agents = [orchestrator, developer, finalizer]
    
    print(f"📋 AGENTES: Orchestrator, Developer, Finalizer\n")
    
    # Criar time com RoundRobinGroupChat
    termination = TextMentionTermination("CONCLUÍDO") | MaxMessageTermination(20)
    
    team = RoundRobinGroupChat(
        participants=agents,
        max_turns=10,
        termination_condition=termination,
    )
    
    # Mensagem introdutória
    intro = f"""TASK: {task_text}

INSTRUÇÕES:
- Orchestrator: coordene e use report_progress
- Developer: implemente e salve artefatos com save_json, save_markdown, etc.
- Finalizer: liste artefatos, gere MANIFEST e encerre dizendo a palavra final

Run Directory: {store.run_dir.absolute()}

COMECE AGORA!"""
    
    # Executar time
    print("=" * 80)
    print("EXECUÇÃO DO TIME")
    print("=" * 80)
    
    try:
        message_count = 0
        async for message in team.run_stream(task=intro):
            message_count += 1
            print(f"\n[Mensagem #{message_count}]")
            print(f"Tipo: {type(message).__name__}")
            print(f"Conteúdo: {message}")
            print("-" * 80)
        
        print("\n" + "=" * 80)
        print(f"EXECUÇÃO CONCLUÍDA - {message_count} mensagens processadas")
        print("=" * 80)
        print(f"\n✅ Artefatos salvos em: {store.run_dir.absolute()}")
        print(f"📄 Veja o MANIFEST.md para lista completa de artefatos.\n")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Execução interrompida pelo usuário.")
        print(f"   Artefatos parciais salvos em: {store.run_dir.absolute()}\n")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n\n❌ ERRO durante execução: {e}")
        print(f"   Artefatos parciais salvos em: {store.run_dir.absolute()}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

