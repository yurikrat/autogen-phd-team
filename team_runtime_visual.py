#!/usr/bin/env python3
"""
Team Runtime Visual: Versão com dashboard web em tempo real e sistema de provocação.
"""

import asyncio
import os
import sys
import webbrowser
import time
from datetime import datetime
from dotenv import load_dotenv

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from autogen_ext.models.openai import OpenAIChatCompletionClient

from tools.artifact_store import init_store
from tools import io_tools
from autogen_core.tools import FunctionTool
from roles import ROLE_MSG
from routing import select_roles
from orchestration import inject_challenge_behavior

# Importar dashboard
try:
    from dashboard.app import start_dashboard_thread, emit_event
    DASHBOARD_AVAILABLE = True
except ImportError:
    DASHBOARD_AVAILABLE = False
    print("⚠️  Dashboard não disponível. Instale: pip install flask flask-socketio")


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
        print("   Uso: python team_runtime_visual.py \"Sua tarefa aqui...\"")
        sys.exit(1)
    
    task_text = " ".join(sys.argv[1:])
    
    # Iniciar dashboard se disponível
    dashboard_url = None
    if DASHBOARD_AVAILABLE:
        print("\n🎨 Iniciando dashboard visual...")
        start_dashboard_thread(host='0.0.0.0', port=5000)
        dashboard_url = "http://localhost:5000"
        print(f"✅ Dashboard disponível em: {dashboard_url}")
        print("   Aguarde 2 segundos e o dashboard abrirá automaticamente...\n")
        time.sleep(2)
        webbrowser.open(dashboard_url)
        emit_event('status', {'status': 'running', 'run_dir': None})
    
    # Inicializar ArtifactStore
    store = init_store()
    print(f"\n🚀 RUN INICIADA: {store.run_dir.absolute()}\n")
    
    if DASHBOARD_AVAILABLE:
        emit_event('status', {'status': 'running', 'run_dir': str(store.run_dir.absolute())})
    
    # Criar modelo de linguagem
    model_client = OpenAIChatCompletionClient(
        model="gpt-4.1-mini",
        api_key=api_key,
    )
    
    # Criar FunctionTools das funções de I/O
    tools = [
        FunctionTool(io_tools.report_progress, description="Reporta progresso ao longo da execução"),
        FunctionTool(io_tools.create_folder, description="Cria pasta dentro do run_dir"),
        FunctionTool(io_tools.save_text, description="Salva arquivo de texto (.txt)"),
        FunctionTool(io_tools.save_markdown, description="Salva arquivo Markdown (.md)"),
        FunctionTool(io_tools.save_json, description="Salva arquivo JSON. Parâmetros: name, data (ou content), relative_path"),
        FunctionTool(io_tools.save_file_from_url, description="Baixa arquivo de URL"),
        FunctionTool(io_tools.save_base64, description="Decodifica base64 e salva"),
        FunctionTool(io_tools.list_artifacts, description="Lista todos os artefatos registrados"),
        FunctionTool(io_tools.zip_run, description="Cria ZIP com todos os artefatos"),
        FunctionTool(io_tools.finalize_run, description="Finaliza a run gerando MANIFEST.md"),
    ]
    
    # Selecionar papéis dinamicamente
    selected_roles = select_roles(task_text)
    print(f"📋 PAPÉIS SELECIONADOS: {', '.join(selected_roles)}\n")
    
    # Criar agentes com comportamento de desafio
    agents = []
    for role_name in selected_roles:
        if role_name not in ROLE_MSG:
            print(f"⚠️  AVISO: Papel '{role_name}' não encontrado em ROLE_MSG. Pulando.")
            continue
        
        # Injetar comportamento de desafio na mensagem de sistema
        enhanced_message = inject_challenge_behavior(role_name, ROLE_MSG[role_name])
        
        agent = AssistantAgent(
            name=role_name,
            model_client=model_client,
            tools=tools,
            system_message=enhanced_message,
        )
        agents.append(agent)
        
        # Registrar agente no dashboard
        if DASHBOARD_AVAILABLE:
            emit_event('message', {
                'source': role_name,
                'content': f'Agente {role_name} ativado',
                'timestamp': datetime.now().isoformat(),
                'type': 'agent_activated'
            })
    
    if not agents:
        print("❌ ERRO: Nenhum agente foi criado. Verifique roles.py e routing.py.")
        sys.exit(1)
    
    # Criar time com RoundRobinGroupChat
    termination = TextMentionTermination("CONCLUÍDO") | MaxMessageTermination(80)
    
    team = RoundRobinGroupChat(
        participants=agents,
        max_turns=len(agents) * 5,
        termination_condition=termination,
    )
    
    # Mensagem introdutória (sem palavra CONCLUÍDO para evitar terminação prematura)
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

4. **PROVOCAÇÃO E EVOLUÇÃO:**
   - DESAFIE as soluções propostas por outros agentes
   - Use frases como: "Você considerou...", "E se...", "Como garantir..."
   - Não aceite soluções medianas - force melhorias
   - Eleve constantemente o nível técnico

5. **Finalização Explícita:**
   - Finalizer deve aguardar até que todos tenham concluído
   - Chamar `list_artifacts()` para listar artefatos
   - Chamar `finalize_run()` para gerar MANIFEST.md
   - Opcionalmente, chamar `zip_run()` para criar bundle
   - Anunciar caminhos locais dos artefatos
   - Encerrar dizendo a palavra final de encerramento

6. **Run Directory:** {store.run_dir.absolute()}

**INÍCIO DA EXECUÇÃO:**
"""
    
    # Executar time
    print("=" * 80)
    print("EXECUÇÃO DO TIME")
    print("=" * 80)
    
    if dashboard_url:
        print(f"\n🎨 Dashboard ao vivo: {dashboard_url}\n")
    
    try:
        message_count = 0
        async for message in team.run_stream(task=intro):
            message_count += 1
            
            # Extrair informações da mensagem
            msg_type = type(message).__name__
            msg_source = getattr(message, 'source', 'system')
            msg_content = getattr(message, 'content', str(message))
            
            # Imprimir no console
            print(f"\n[{message_count}] {msg_source} ({msg_type})")
            if isinstance(msg_content, str) and len(msg_content) < 500:
                print(f"  {msg_content[:200]}...")
            
            # Enviar para dashboard
            if DASHBOARD_AVAILABLE:
                # Detectar desafios
                is_challenge = any(word in str(msg_content).lower() for word in [
                    'desafio', 'considerou', 'e se', 'como garantir', 'questiono'
                ])
                
                # Detectar melhorias
                is_improvement = any(word in str(msg_content).lower() for word in [
                    'melhoria', 'otimização', 'aprimoramento', 'correção'
                ])
                
                emit_event('message', {
                    'source': msg_source,
                    'content': str(msg_content)[:500],  # Limitar tamanho
                    'timestamp': datetime.now().isoformat(),
                    'type': msg_type,
                    'is_challenge': is_challenge,
                    'is_improvement': is_improvement,
                })
                
                if is_challenge:
                    emit_event('challenge', {'from': msg_source})
                
                if is_improvement:
                    emit_event('improvement', {'by': msg_source})
                
                # Detectar artefatos criados
                if 'save_' in str(msg_content) and 'status' in str(msg_content):
                    try:
                        # Tentar extrair informações do artefato
                        if hasattr(message, 'content') and isinstance(message.content, str):
                            if 'file' in message.content:
                                emit_event('artifact', {
                                    'name': 'Artefato criado',
                                    'kind': 'file',
                                    'path': 'Ver progress.log',
                                    'timestamp': datetime.now().isoformat(),
                                })
                    except:
                        pass
        
        print("\n" + "=" * 80)
        print(f"EXECUÇÃO CONCLUÍDA - {message_count} mensagens processadas")
        print("=" * 80)
        print(f"\n✅ Artefatos salvos em: {store.run_dir.absolute()}")
        print(f"📄 Veja o MANIFEST.md para lista completa de artefatos.\n")
        
        if DASHBOARD_AVAILABLE:
            emit_event('status', {'status': 'completed'})
            print(f"\n🎨 Dashboard ainda disponível em: {dashboard_url}")
            print("   Pressione Ctrl+C para encerrar.\n")
            
            # Manter o programa rodando para o dashboard continuar acessível
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\n\n👋 Encerrando...")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Execução interrompida pelo usuário.")
        print(f"   Artefatos parciais salvos em: {store.run_dir.absolute()}\n")
        if DASHBOARD_AVAILABLE:
            emit_event('status', {'status': 'error'})
        sys.exit(1)
    
    except Exception as e:
        print(f"\n\n❌ ERRO durante execução: {e}")
        print(f"   Artefatos parciais salvos em: {store.run_dir.absolute()}\n")
        if DASHBOARD_AVAILABLE:
            emit_event('status', {'status': 'error'})
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

