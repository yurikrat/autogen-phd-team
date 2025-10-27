#!/usr/bin/env python3
"""
Team Runtime Intelligent: Versão com provocação contextual e validação inteligente.
Sistema que funciona como um time humano real, não com perguntas pré-prontas.
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

from tools.artifact_store import init_store, get_store
from tools import io_tools
from autogen_core.tools import FunctionTool
from roles import ROLE_MSG
from routing import select_roles
from intelligence.contextual_challenge import get_challenge_system
from intelligence.artifact_validator import get_validator

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
        print("   Uso: python team_runtime_intelligent.py \"Sua tarefa aqui...\"")
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
    
    # Inicializar sistemas de inteligência
    challenge_system = get_challenge_system()
    validator = get_validator()
    
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
    
    # Criar agentes com mensagens aprimoradas
    agents = []
    for role_name in selected_roles:
        if role_name not in ROLE_MSG:
            print(f"⚠️  AVISO: Papel '{role_name}' não encontrado em ROLE_MSG. Pulando.")
            continue
        
        # Adicionar instruções de feedback contínuo e provocação contextual
        enhanced_message = ROLE_MSG[role_name] + """

**IMPORTANTE - COMPORTAMENTO INTELIGENTE:**

1. **Feedback Contínuo:** Use report_progress() CONSTANTEMENTE
   - Seja específico: "Criando endpoint GET /users com paginação"
   - Reporte decisões: "Escolhi PostgreSQL por suportar JSON nativo"
   - Reporte bloqueios: "Preciso de definição de schema antes de continuar"

2. **Provocação Contextual:** Analise o que outros agentes estão fazendo
   - Se ver uma decisão técnica, QUESTIONE os trade-offs
   - Se ver código sem testes, EXIJA testes
   - Se ver API sem segurança, APONTE os riscos
   - Seja ESPECÍFICO ao contexto, não genérico

3. **Validação Constante:** Garanta qualidade
   - Verifique se artefatos fazem sentido para a tarefa
   - Valide se código está completo e funcional
   - Confirme que documentação está clara

4. **Colaboração Real:** Funcione como um time humano
   - Construa em cima do trabalho dos outros
   - Desafie quando necessário
   - Melhore iterativamente
   - Não aceite soluções medianas

**LEMBRE-SE:** Você é um profissional PhD/Nobel. Exija excelência!
"""
        
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
    # Usar apenas MaxMessageTermination para dar tempo aos agentes
    termination = MaxMessageTermination(50)
    
    team = RoundRobinGroupChat(
        participants=agents,
        max_turns=len(agents) * 10,
        termination_condition=termination,
    )
    
    # Mensagem introdutória
    intro = f"""
**TAREFA:** {task_text}

**INSTRUÇÕES:**

1. **Feedback Contínuo:** Use report_progress() CONSTANTEMENTE para reportar o que estão fazendo

2. **Artefatos Concretos:** Criem TODOS os artefatos necessários para completar a tarefa
   - Código completo e funcional
   - Testes adequados
   - Documentação clara
   - Configurações necessárias

3. **Provocação Contextual:** Desafiem-se mutuamente baseado no CONTEXTO REAL
   - Não usem perguntas genéricas
   - Analisem o que foi dito e QUESTIONEM especificamente
   - Apontem riscos, gaps e oportunidades de melhoria

4. **Validação de Qualidade:** Garantam que o que criaram é BOM
   - Código funciona?
   - Testes cobrem casos importantes?
   - Documentação está clara?
   - Segurança está adequada?

5. **Finalização:** Ao concluir, Finalizer deve:
   - Listar todos os artefatos com list_artifacts()
   - Gerar MANIFEST.md com finalize_run()
   - Confirmar que a tarefa foi completada com qualidade

**Run Directory:** {store.run_dir.absolute()}

**COMECEM AGORA!**
"""
    
    # Executar time
    print("=" * 80)
    print("EXECUÇÃO DO TIME COM INTELIGÊNCIA CONTEXTUAL")
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
            msg_content = str(getattr(message, 'content', message))
            
            # Imprimir no console
            print(f"\n[{message_count}] {msg_source} ({msg_type})")
            if len(msg_content) < 500:
                print(f"  {msg_content[:300]}")
            
            # Analisar contexto e gerar desafios inteligentes
            artifacts = store.list()
            analysis = challenge_system.analyze_context(msg_content, msg_source, artifacts)
            
            # Se houver oportunidades de desafio, mostrar
            if analysis["opportunities"]:
                print(f"\n  🧠 Análise contextual detectou {len(analysis['opportunities'])} oportunidade(s) de melhoria")
                for opp in analysis["opportunities"][:2]:  # Mostrar até 2
                    print(f"     • {opp['type']}: {opp['reason']}")
            
            # Enviar para dashboard
            if DASHBOARD_AVAILABLE:
                is_challenge = "🎯" in msg_content or any(
                    opp["type"] in ["technical_review", "security_review", "performance_review"]
                    for opp in analysis.get("opportunities", [])
                )
                
                is_improvement = "melhoria" in msg_content.lower() or "otimização" in msg_content.lower()
                
                emit_event('message', {
                    'source': msg_source,
                    'content': msg_content[:500],
                    'timestamp': datetime.now().isoformat(),
                    'type': msg_type,
                    'is_challenge': is_challenge,
                    'is_improvement': is_improvement,
                    'opportunities': analysis.get("opportunities", [])
                })
                
                if is_challenge:
                    emit_event('challenge', {'from': msg_source})
                
                if is_improvement:
                    emit_event('improvement', {'by': msg_source})
                
                # Detectar artefatos criados
                if 'save_' in msg_content and 'status' in msg_content:
                    emit_event('artifact', {
                        'name': 'Artefato criado',
                        'kind': 'file',
                        'timestamp': datetime.now().isoformat(),
                    })
        
        print("\n" + "=" * 80)
        print(f"EXECUÇÃO CONCLUÍDA - {message_count} mensagens processadas")
        print("=" * 80)
        
        # Validar artefatos automaticamente
        print("\n🔍 Validando qualidade dos artefatos...\n")
        artifacts = store.list()
        validation = validator.validate_artifacts_for_task(task_text, artifacts)
        
        print(f"📊 Score de Qualidade: {validation['score']:.1%}\n")
        for feedback in validation["feedback"]:
            print(f"  {feedback}")
        
        if validation["quality_issues"]:
            print("\n⚠️ Problemas de Qualidade Detectados:")
            for issue in validation["quality_issues"]:
                print(f"  {issue}")
        
        suggestions = validator.generate_improvement_suggestions(validation)
        if suggestions:
            print("\n💡 Sugestões de Melhoria:")
            for suggestion in suggestions:
                print(f"  {suggestion}")
        
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

