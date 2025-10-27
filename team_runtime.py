#!/usr/bin/env python3
"""
Team Runtime: CLI principal para executar o time de agentes AutoGen.
Aceita task via argumento, cria run_dir, orquestra agentes e entrega artefatos.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient

from tools.artifact_store import init_store
from tools import io_tools
from roles import ROLE_MSG
from routing import select_roles

# Importar funções de I/O para criar FunctionTools
from autogen_core.tools import FunctionTool


async def main():
    # Carregar variáveis de ambiente
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ ERRO: OPENAI_API_KEY não encontrada no .env")
        print("   Copie .env.example para .env e configure sua chave.")
        sys.exit(1)
    
    # Verificar se task foi fornecida
    if len(sys.argv) < 2:
        print("❌ ERRO: Task não fornecida.")
        print("   Uso: python team_runtime.py \"Sua tarefa aqui...\"")
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
        FunctionTool(io_tools.create_folder, description="Cria uma pasta dentro do run_dir"),
        FunctionTool(io_tools.save_text, description="Salva arquivo de texto (.txt)"),
        FunctionTool(io_tools.save_markdown, description="Salva arquivo Markdown (.md)"),
        FunctionTool(io_tools.save_json, description="Salva arquivo JSON (.json)"),
        FunctionTool(io_tools.save_file_from_url, description="Baixa arquivo de URL e salva"),
        FunctionTool(io_tools.save_base64, description="Decodifica base64 e salva arquivo"),
        FunctionTool(io_tools.list_artifacts, description="Lista todos os artefatos registrados"),
        FunctionTool(io_tools.zip_run, description="Cria arquivo ZIP com todos os artefatos"),
        FunctionTool(io_tools.finalize_run, description="Finaliza a run gerando MANIFEST.md"),
    ]
    
    # Selecionar papéis dinamicamente
    selected_roles = select_roles(task_text)
    print(f"📋 PAPÉIS SELECIONADOS: {', '.join(selected_roles)}\n")
    
    # Criar agentes
    agents = []
    for role_name in selected_roles:
        if role_name not in ROLE_MSG:
            print(f"⚠️  AVISO: Papel '{role_name}' não encontrado em ROLE_MSG. Pulando.")
            continue
        
        agent = AssistantAgent(
            name=role_name,
            model_client=model_client,
            tools=tools,
            system_message=ROLE_MSG[role_name],
        )
        agents.append(agent)
    
    if not agents:
        print("❌ ERRO: Nenhum agente foi criado. Verifique roles.py e routing.py.")
        sys.exit(1)
    
    # Criar time com RoundRobinGroupChat
    termination = TextMentionTermination("CONCLUÍDO") | MaxMessageTermination(80)
    
    team = RoundRobinGroupChat(
        participants=agents,
        max_turns=len(agents) * 5,  # Cada agente pode falar até 5 vezes
        termination_condition=termination,
    )
    
    # Mensagem introdutória com regras explícitas (sem a palavra CONCLUÍDO para evitar terminação prematura)
    intro = f"""
**TASK:** {task_text}

**REGRAS DE EXECUÇÃO:**

1. **Feedback Contínuo:** Use `report_progress(stage, message)` frequentemente para reportar progresso, decisões e bloqueios.

2. **Artefatos Concretos:** Salve TODOS os artefatos relevantes usando as tools SAVE_* (save_text, save_markdown, save_json, save_file_from_url, save_base64).

3. **Colaboração Estruturada:** 
   - AI_Orchestrator coordena e decompõe a task
   - Project_Manager define marcos e monitora progresso
   - Tech_Architect define arquitetura e padrões
   - Papéis especializados implementam suas partes
   - Finalizer consolida tudo ao final

4. **Finalização Explícita:**
   - Finalizer deve aguardar até que todos tenham concluído
   - Chamar `list_artifacts()` para listar artefatos
   - Chamar `finalize_run()` para gerar MANIFEST.md
   - Opcionalmente, chamar `zip_run()` para criar bundle
   - Anunciar caminhos locais dos artefatos
   - Encerrar dizendo a palavra final de encerramento

5. **Run Directory:** {store.run_dir.absolute()}

**INÍCIO DA EXECUÇÃO:**
"""
    
    # Executar time
    print("=" * 80)
    print("EXECUÇÃO DO TIME")
    print("=" * 80)
    
    try:
        await Console(team.run_stream(task=intro))
        print("\n" + "=" * 80)
        print("EXECUÇÃO CONCLUÍDA")
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
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

