#!/usr/bin/env python3
"""
Team Runtime Visual: Versão com dashboard web em tempo real e sistema de provocação.
"""

import asyncio
import os
import sys
import webbrowser
import time
from datetime import datetime, timezone
import threading
import contextlib
from openai import OpenAI
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
    # Cliente para diagnóstico (ping OpenAI)
    try:
        diag_client = OpenAI(api_key=api_key)
    except Exception:
        diag_client = None
    
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
   - Tech_Architect define arquitetura, padrões E valida dependências técnicas
   - Papéis especializados implementam suas partes
   - Code_Validator valida completude e executabilidade do código
   - Finalizer consolida tudo ao final

4. **PROVOCAÇÃO E EVOLUÇÃO:**
   - DESAFIE as soluções propostas por outros agentes
   - Use frases como: "Você considerou...", "E se...", "Como garantir..."
   - Não aceite soluções medianas - force melhorias
   - Eleve constantemente o nível técnico
   - Tech_Architect SEMPRE pergunta: "Onde estão os arquivos importados?"
   - Code_Validator SEMPRE valida imports e dependências

5. **VALIDAÇÃO DE CÓDIGO (Code_Validator):**
   - APÓS implementação, Code_Validator DEVE validar:
     ✅ Todos os imports têm arquivos correspondentes
     ✅ Arquivos de config necessários foram criados (database.py, config.py, etc)
     ✅ Código é executável sem ModuleNotFoundError
   - Se faltar arquivos, Code_Validator EXIGE criação antes de prosseguir

7. **Finalização Explícita:**
   - Finalizer deve aguardar até que todos tenham concluído
   - Chamar `list_artifacts()` para listar artefatos
   - Chamar `finalize_run()` para gerar MANIFEST.md
   - Opcionalmente, chamar `zip_run()` para criar bundle
   - Anunciar caminhos locais dos artefatos
   - Encerrar dizendo a palavra final de encerramento

8. **Run Directory:** {store.run_dir.absolute()}

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
        start_ts = time.time()
        last_msg_ts = time.time()
        # Defaults ajustados para melhor visibilidade: 10s/30s (pode sobrescrever via env)
        heartbeat_interval = int(os.getenv("TRACE_INTERVAL_SECS", "10"))
        stall_secs = int(os.getenv("DIAG_STALL_SECS", "30"))
        diag_enabled = os.getenv("DIAG_PING_ENABLED", "1") != "0"

        stop_event = threading.Event()

        def _heartbeat_thread():
            """Thread de heartbeat: não depende do event loop (mais resiliente)."""
            try:
                while not stop_event.is_set():
                    time.sleep(heartbeat_interval)
                    now = time.time()
                    uptime = int(now - start_ts)
                    last_age = int(now - last_msg_ts)
                    artifacts_count = len(store.artifacts)
                    # Log para progress.log
                    try:
                        io_tools.report_progress(
                            stage="Heartbeat",
                            message=(
                                f"msgs={message_count}, artifacts={artifacts_count}, "
                                f"last_msg_age={last_age}s, uptime={uptime}s"
                            )
                        )
                    except Exception:
                        pass
                    # Métricas para dashboard
                    if DASHBOARD_AVAILABLE:
                        try:
                            emit_event('metric', {
                                'heartbeat_ts': datetime.now(timezone.utc).isoformat(),
                                'message_count': message_count,
                                'artifact_count': artifacts_count,
                                'last_message_age_sec': last_age,
                                'uptime_sec': uptime,
                            })
                        except Exception:
                            pass
                    # Diagnóstico de stall (quando sem mensagens por muito tempo)
                    if diag_enabled and diag_client is not None and last_age >= stall_secs:
                        t0 = time.time()
                        status = "ok"
                        err_str = None
                        try:
                            diag_client.chat.completions.create(
                                model="gpt-4.1-mini",
                                messages=[{"role": "user", "content": "ping"}],
                                max_tokens=1,
                            )
                        except Exception as e:
                            status = "error"
                            err_str = str(e)[:300]
                        latency_ms = int((time.time() - t0) * 1000)

                        try:
                            io_tools.report_progress(
                                stage="Diag",
                                message=(
                                    f"openai_ping status={status} latency_ms={latency_ms}"
                                    + (f" error={err_str}" if err_str else "")
                                )
                            )
                        except Exception:
                            pass
                        if DASHBOARD_AVAILABLE:
                            try:
                                emit_event('metric', {
                                    'diagnostic': {
                                        'status': status,
                                        'latency_ms': latency_ms,
                                        'error': err_str,
                                        'ts': datetime.now(timezone.utc).isoformat(),
                                    }
                                })
                            except Exception:
                                pass
            except Exception as e:
                # Garantir que qualquer erro no heartbeat seja logado, não terminando o processo principal
                try:
                    io_tools.report_progress("HeartbeatError", f"{type(e).__name__}: {str(e)[:300]}")
                except Exception:
                    pass

        hb_thread = threading.Thread(target=_heartbeat_thread, name="heartbeat", daemon=True)
        hb_thread.start()
        # Logar configuração de tracing
        try:
            io_tools.report_progress(
                stage="Config",
                message=(
                    f"TRACE_INTERVAL_SECS={heartbeat_interval}, DIAG_STALL_SECS={stall_secs}, DIAG_PING_ENABLED={int(diag_enabled)}"
                )
            )
        except Exception:
            pass
        async for message in team.run_stream(task=intro):
            message_count += 1
            last_msg_ts = time.time()
            
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
        
        # Encerrar heartbeat thread
        stop_event.set()
        hb_thread.join(timeout=2.0)

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

