"""
Chatbot Interativo para Orquestração de Agentes.
Interface conversacional para você e diretores interagirem com o time.
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Adicionar path do projeto
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.tools import FunctionTool

from tools.artifact_store import init_store, get_store
from tools import io_tools
from roles import ROLE_MSG
from routing import select_roles
from intelligence.contextual_challenge import get_challenge_system
from intelligence.artifact_validator import get_validator


class InteractiveChatbot:
    """
    Chatbot interativo que orquestra o time de agentes.
    Permite interação contínua e feedback em tempo real.
    """
    
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY não encontrada no .env")
        
        self.store = None
        self.model_client = None
        self.agents = []
        self.team = None
        self.challenge_system = get_challenge_system()
        self.validator = get_validator()
        self.conversation_history = []
        self.current_task = None
        self.task_completed = False
    
    def print_header(self):
        """Imprime header do chatbot."""
        print("\n" + "=" * 80)
        print("🎼 AutoGen PhD Team - Chatbot Interativo")
        print("=" * 80)
        print("\n💬 Converse com o time de agentes de TI de nível PhD/Nobel")
        print("📊 Acompanhe o progresso em tempo real")
        print("🎯 Dê feedback e ajuste a direção conforme necessário")
        print("\n" + "-" * 80)
        print("Comandos disponíveis:")
        print("  /status    - Ver status atual da tarefa")
        print("  /artifacts - Listar artefatos criados")
        print("  /validate  - Validar qualidade dos artefatos")
        print("  /feedback  - Dar feedback ao time")
        print("  /help      - Mostrar ajuda")
        print("  /exit      - Sair")
        print("-" * 80 + "\n")
    
    def initialize_team(self, task: str):
        """Inicializa o time de agentes para a tarefa."""
        print(f"\n🚀 Inicializando time para tarefa: {task}\n")
        
        # Inicializar store
        self.store = init_store()
        print(f"📁 Artefatos serão salvos em: {self.store.run_dir.absolute()}\n")
        
        # Criar modelo
        self.model_client = OpenAIChatCompletionClient(
            model="gpt-4.1-mini",
            api_key=self.api_key,
        )
        
        # Criar tools
        tools = [
            FunctionTool(io_tools.report_progress, description="Reporta progresso"),
            FunctionTool(io_tools.create_folder, description="Cria pasta"),
            FunctionTool(io_tools.save_text, description="Salva texto"),
            FunctionTool(io_tools.save_markdown, description="Salva Markdown"),
            FunctionTool(io_tools.save_json, description="Salva JSON (params: name, data ou content)"),
            FunctionTool(io_tools.save_file_from_url, description="Baixa de URL"),
            FunctionTool(io_tools.save_base64, description="Decodifica base64"),
            FunctionTool(io_tools.list_artifacts, description="Lista artefatos"),
            FunctionTool(io_tools.zip_run, description="Cria ZIP"),
            FunctionTool(io_tools.finalize_run, description="Finaliza com MANIFEST"),
        ]
        
        # Selecionar papéis
        selected_roles = select_roles(task)
        print(f"👥 Agentes selecionados: {', '.join(selected_roles)}\n")
        
        # Criar agentes
        self.agents = []
        for role_name in selected_roles:
            if role_name not in ROLE_MSG:
                continue
            
            # Adicionar instrução de feedback contínuo
            enhanced_message = ROLE_MSG[role_name] + """

**IMPORTANTE - FEEDBACK CONTÍNUO:**
- Use report_progress() FREQUENTEMENTE para reportar o que está fazendo
- Seja específico: "Criando endpoint GET /users com paginação"
- Reporte decisões: "Escolhi PostgreSQL por suportar JSON nativo"
- Reporte bloqueios: "Preciso de definição de schema antes de continuar"
- Reporte conclusões: "Endpoint /users implementado e testado"

O usuário está acompanhando em tempo real e pode dar feedback a qualquer momento.
"""
            
            agent = AssistantAgent(
                name=role_name,
                model_client=self.model_client,
                tools=tools,
                system_message=enhanced_message,
            )
            self.agents.append(agent)
        
        # Criar team
        termination = TextMentionTermination("TAREFA_FINALIZADA") | MaxMessageTermination(100)
        self.team = RoundRobinGroupChat(
            participants=self.agents,
            max_turns=len(self.agents) * 10,
            termination_condition=termination,
        )
        
        self.current_task = task
        print("✅ Time inicializado e pronto!\n")
    
    async def execute_task_with_feedback(self, task: str):
        """Executa tarefa com feedback contínuo."""
        intro = f"""
**TAREFA:** {task}

**INSTRUÇÕES:**
1. Usem report_progress() CONSTANTEMENTE para reportar o que estão fazendo
2. Desafiem-se mutuamente quando virem oportunidades de melhoria
3. Criem TODOS os artefatos necessários para completar a tarefa
4. Validem a qualidade do que criaram
5. Ao final, Finalizer deve chamar finalize_run() e dizer "TAREFA_FINALIZADA"

**IMPORTANTE:** O usuário está acompanhando em tempo real e pode dar feedback.

**Run Directory:** {self.store.run_dir.absolute()}

**COMECEM AGORA!**
"""
        
        print("\n" + "=" * 80)
        print("🎬 EXECUÇÃO INICIADA")
        print("=" * 80 + "\n")
        
        message_count = 0
        
        try:
            async for message in self.team.run_stream(task=intro):
                message_count += 1
                
                msg_type = type(message).__name__
                msg_source = getattr(message, 'source', 'system')
                msg_content = str(getattr(message, 'content', message))
                
                # Armazenar na história
                self.conversation_history.append({
                    "count": message_count,
                    "source": msg_source,
                    "type": msg_type,
                    "content": msg_content,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Exibir feedback visual
                self._display_message(message_count, msg_source, msg_type, msg_content)
                
                # Analisar contexto e gerar desafios inteligentes
                await self._analyze_and_challenge(msg_source, msg_content)
                
                # Permitir interrupção para feedback do usuário
                # (em implementação real, seria via WebSocket ou thread separada)
        
        except Exception as e:
            print(f"\n❌ Erro durante execução: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 80)
        print(f"✅ EXECUÇÃO CONCLUÍDA - {message_count} mensagens")
        print("=" * 80 + "\n")
        
        # Validar artefatos automaticamente
        await self.validate_artifacts()
    
    def _display_message(self, count: int, source: str, msg_type: str, content: str):
        """Exibe mensagem formatada."""
        # Detectar tipo de mensagem
        is_progress = "report_progress" in content or "stage" in content.lower()
        is_challenge = "🎯" in content or "desafio" in content.lower()
        is_artifact = "save_" in content and "status" in content
        
        # Escolher emoji e cor
        if is_progress:
            emoji = "📊"
            color = "\033[94m"  # Azul
        elif is_challenge:
            emoji = "🎯"
            color = "\033[93m"  # Amarelo
        elif is_artifact:
            emoji = "📦"
            color = "\033[92m"  # Verde
        else:
            emoji = "💬"
            color = "\033[0m"  # Normal
        
        # Exibir
        print(f"{color}{emoji} [{count}] {source}{'\033[0m'}")
        
        # Extrair parte relevante do conteúdo
        if len(content) > 300:
            content_preview = content[:300] + "..."
        else:
            content_preview = content
        
        # Extrair mensagens de progresso
        if "message" in content and "stage" in content:
            try:
                # Tentar extrair JSON
                import json
                if "{" in content:
                    start = content.index("{")
                    end = content.rindex("}") + 1
                    data = json.loads(content[start:end])
                    if "message" in data:
                        print(f"   {data.get('stage', 'Info')}: {data['message']}")
                        return
            except:
                pass
        
        print(f"   {content_preview}\n")
    
    async def _analyze_and_challenge(self, source: str, content: str):
        """Analisa contexto e gera desafios inteligentes."""
        # Pegar artefatos atuais
        artifacts = self.store.list()
        
        # Analisar contexto
        analysis = self.challenge_system.analyze_context(content, source, artifacts)
        
        # Se houver oportunidades, gerar desafio
        if analysis["opportunities"]:
            # Escolher papel adequado para desafiar
            challenger_roles = {
                "technical_review": "Tech_Architect",
                "security_review": "SecOps",
                "performance_review": "Performance_Engineer",
                "scalability_review": "Tech_Architect",
                "testing_gap": "QA_Engineer",
                "documentation_gap": "Docs_Specialist",
                "error_handling_gap": "QA_Engineer",
            }
            
            for opp in analysis["opportunities"][:1]:  # Apenas primeira oportunidade
                challenger = challenger_roles.get(opp["type"])
                if challenger and challenger != source:
                    challenge = self.challenge_system.generate_contextual_challenge(
                        challenger, source, analysis, content
                    )
                    if challenge:
                        print(f"\n{challenge}\n")
    
    async def validate_artifacts(self):
        """Valida qualidade dos artefatos criados."""
        print("\n" + "=" * 80)
        print("🔍 VALIDAÇÃO DE ARTEFATOS")
        print("=" * 80 + "\n")
        
        artifacts = self.store.list()
        validation = self.validator.validate_artifacts_for_task(
            self.current_task,
            artifacts
        )
        
        print(f"📊 Score de Qualidade: {validation['score']:.1%}\n")
        
        for feedback in validation["feedback"]:
            print(f"  {feedback}")
        
        if validation["quality_issues"]:
            print("\n⚠️ Problemas de Qualidade:")
            for issue in validation["quality_issues"]:
                print(f"  {issue}")
        
        # Gerar sugestões
        suggestions = self.validator.generate_improvement_suggestions(validation)
        if suggestions:
            print("\n💡 Sugestões de Melhoria:")
            for suggestion in suggestions:
                print(f"  {suggestion}")
        
        print("\n" + "=" * 80 + "\n")
        
        return validation
    
    def show_status(self):
        """Mostra status atual."""
        print("\n" + "=" * 80)
        print("📊 STATUS ATUAL")
        print("=" * 80)
        print(f"\n📋 Tarefa: {self.current_task}")
        print(f"👥 Agentes: {len(self.agents)}")
        print(f"💬 Mensagens: {len(self.conversation_history)}")
        
        artifacts = self.store.list() if self.store else []
        print(f"📦 Artefatos: {len(artifacts)}")
        
        if artifacts:
            print("\n📂 Artefatos criados:")
            for art in artifacts:
                print(f"  • {art['name']} ({art['kind']})")
        
        print("\n" + "=" * 80 + "\n")
    
    def show_artifacts(self):
        """Lista artefatos detalhadamente."""
        print("\n" + "=" * 80)
        print("📦 ARTEFATOS CRIADOS")
        print("=" * 80 + "\n")
        
        artifacts = self.store.list() if self.store else []
        
        if not artifacts:
            print("  Nenhum artefato criado ainda.\n")
            return
        
        for i, art in enumerate(artifacts, 1):
            print(f"{i}. {art['name']}")
            print(f"   Tipo: {art['kind']}")
            print(f"   Caminho: {art['path']}")
            if art.get('meta'):
                print(f"   Meta: {art['meta']}")
            print()
        
        print("=" * 80 + "\n")
    
    async def run(self):
        """Loop principal do chatbot."""
        self.print_header()
        
        # Pegar tarefa inicial
        print("💬 Olá! Sou o orquestrador do time de TI PhD/Nobel.")
        print("   Diga-me o que você precisa e eu coordenarei o time.\n")
        
        task = input("📋 Qual é a tarefa? > ").strip()
        
        if not task:
            print("❌ Tarefa não pode ser vazia.")
            return
        
        # Inicializar time
        self.initialize_team(task)
        
        # Executar tarefa
        await self.execute_task_with_feedback(task)
        
        # Loop de interação pós-execução
        while True:
            print("\n💬 O que mais posso fazer?")
            print("   (Digite /help para ver comandos ou /exit para sair)\n")
            
            user_input = input("> ").strip()
            
            if not user_input:
                continue
            
            if user_input.startswith("/"):
                await self._handle_command(user_input)
            else:
                print("💡 Use /help para ver comandos disponíveis.")
    
    async def _handle_command(self, command: str):
        """Processa comandos do usuário."""
        cmd = command.lower().split()[0]
        
        if cmd == "/exit":
            print("\n👋 Até logo! Artefatos salvos em:")
            print(f"   {self.store.run_dir.absolute()}\n")
            sys.exit(0)
        
        elif cmd == "/status":
            self.show_status()
        
        elif cmd == "/artifacts":
            self.show_artifacts()
        
        elif cmd == "/validate":
            await self.validate_artifacts()
        
        elif cmd == "/help":
            self.print_header()
        
        else:
            print(f"❌ Comando desconhecido: {cmd}")
            print("   Use /help para ver comandos disponíveis.")


async def main():
    """Função principal."""
    chatbot = InteractiveChatbot()
    await chatbot.run()


if __name__ == "__main__":
    asyncio.run(main())

