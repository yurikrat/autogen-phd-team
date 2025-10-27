"""
Interface Web Completa para AutoGen PhD Team.
Abstrai completamente os comandos Python - tudo via web.
"""

from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime
import threading
import uuid

# Adicionar path do projeto
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import MaxMessageTermination
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.tools import FunctionTool

from tools.artifact_store import init_store, get_store, ArtifactStore
from tools import io_tools
from roles import ROLE_MSG
from routing import select_roles
from intelligence.contextual_challenge import get_challenge_system
from intelligence.artifact_validator import get_validator

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'autogen-phd-team-secret-key')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Estado global das execuções
executions = {}


class TaskExecution:
    """Gerencia uma execução de tarefa."""
    
    def __init__(self, task_id: str, task_text: str):
        self.task_id = task_id
        self.task_text = task_text
        self.status = "initializing"  # initializing, running, completed, error
        self.messages = []
        self.artifacts = []
        self.agents = []
        self.store = None
        self.validation_result = None
        self.start_time = datetime.now()
        self.end_time = None
    
    async def execute(self):
        """Executa a tarefa."""
        try:
            self.status = "running"
            self._emit_status()
            
            # Inicializar store
            self.store = init_store()
            
            # Criar modelo
            api_key = os.getenv("OPENAI_API_KEY")
            model_client = OpenAIChatCompletionClient(
                model="gpt-4.1-mini",
                api_key=api_key,
            )
            
            # Criar tools
            tools = [
                FunctionTool(io_tools.report_progress, description="Reporta progresso"),
                FunctionTool(io_tools.save_text, description="Salva texto"),
                FunctionTool(io_tools.save_markdown, description="Salva Markdown"),
                FunctionTool(io_tools.save_json, description="Salva JSON (params: name, data ou content)"),
                FunctionTool(io_tools.list_artifacts, description="Lista artefatos"),
                FunctionTool(io_tools.finalize_run, description="Finaliza com MANIFEST"),
            ]
            
            # Selecionar papéis (máximo 5 para não ficar muito lento)
            all_roles = select_roles(self.task_text)
            selected_roles = all_roles[:5] if len(all_roles) > 5 else all_roles
            
            # Criar agentes com instruções MUITO DIRETAS
            agents = []
            for role_name in selected_roles:
                if role_name not in ROLE_MSG:
                    continue
                
                # Mensagem SUPER DIRETA - SEM PEDIR MAIS INFORMAÇÕES
                direct_message = f"""Você é o **{role_name}**.

**SUA MISSÃO:** Executar a tarefa IMEDIATAMENTE sem pedir mais informações.

**REGRAS ESTRITAS:**
1. NÃO pergunte "qual framework?" - ESCOLHA um (FastAPI, Flask, Express)
2. NÃO pergunte "quais requisitos?" - USE padrões da indústria
3. NÃO fique aguardando - FAÇA AGORA
4. Use report_progress() para mostrar o que está fazendo
5. Crie artefatos concretos com save_*()

**COMPORTAMENTO:**
- Seja PROATIVO e tome decisões
- Implemente COMPLETAMENTE
- Não deixe nada pela metade
- Finalize o que começou

**IMPORTANTE:** A tarefa já tem TODAS as informações necessárias. EXECUTE!
"""
                
                agent = AssistantAgent(
                    name=role_name,
                    model_client=model_client,
                    tools=tools,
                    system_message=direct_message,
                )
                agents.append(agent)
                self.agents.append(role_name)
            
            # Criar team
            termination = MaxMessageTermination(30)  # Máximo 30 mensagens
            team = RoundRobinGroupChat(
                participants=agents,
                max_turns=len(agents) * 3,  # 3 rodadas por agente
                termination_condition=termination,
            )
            
            # Mensagem introdutória SUPER DIRETA
            intro = f"""
**TAREFA:** {self.task_text}

**INSTRUÇÕES DIRETAS:**

1. EXECUTEM IMEDIATAMENTE - não peçam mais informações
2. TOMEM DECISÕES - escolham tecnologias padrão da indústria
3. CRIEM ARTEFATOS - código, docs, testes COMPLETOS
4. REPORTEM PROGRESSO - use report_progress() constantemente
5. FINALIZEM - quando terminar, Finalizer chama finalize_run()

**TECNOLOGIAS PADRÃO (use estas):**
- Backend: FastAPI ou Flask
- Frontend: React ou Vue
- Database: PostgreSQL
- Cache: Redis
- Testes: pytest ou jest

**NÃO PEÇAM MAIS INFORMAÇÕES - EXECUTEM AGORA!**

Run Directory: {self.store.run_dir.absolute()}
"""
            
            # Executar
            message_count = 0
            async for message in team.run_stream(task=intro):
                message_count += 1
                
                msg_type = type(message).__name__
                msg_source = getattr(message, 'source', 'system')
                msg_content = str(getattr(message, 'content', message))[:500]
                
                # Armazenar mensagem
                self.messages.append({
                    "count": message_count,
                    "source": msg_source,
                    "type": msg_type,
                    "content": msg_content,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Emitir para frontend
                self._emit_message(msg_source, msg_content, msg_type)
                
                # Atualizar artefatos
                if 'save_' in msg_content:
                    self.artifacts = self.store.list()
                    self._emit_artifacts()
            
            # Validar artefatos
            validator = get_validator()
            self.validation_result = validator.validate_artifacts_for_task(
                self.task_text,
                self.store.list()
            )
            
            self.status = "completed"
            self.end_time = datetime.now()
            self._emit_status()
            self._emit_validation()
            
        except Exception as e:
            self.status = "error"
            self.end_time = datetime.now()
            self._emit_error(str(e))
    
    def _emit_status(self):
        """Emite status para frontend."""
        socketio.emit('status_update', {
            'task_id': self.task_id,
            'status': self.status,
            'agents': self.agents,
            'message_count': len(self.messages),
            'artifact_count': len(self.artifacts),
        }, room=self.task_id)
    
    def _emit_message(self, source: str, content: str, msg_type: str):
        """Emite mensagem para frontend."""
        socketio.emit('new_message', {
            'task_id': self.task_id,
            'source': source,
            'content': content,
            'type': msg_type,
            'timestamp': datetime.now().isoformat()
        }, room=self.task_id)
    
    def _emit_artifacts(self):
        """Emite lista de artefatos para frontend."""
        socketio.emit('artifacts_update', {
            'task_id': self.task_id,
            'artifacts': self.artifacts
        }, room=self.task_id)
    
    def _emit_validation(self):
        """Emite resultado da validação para frontend."""
        socketio.emit('validation_result', {
            'task_id': self.task_id,
            'validation': self.validation_result
        }, room=self.task_id)
    
    def _emit_error(self, error: str):
        """Emite erro para frontend."""
        socketio.emit('execution_error', {
            'task_id': self.task_id,
            'error': error
        }, room=self.task_id)


@app.route('/')
def index():
    """Página principal."""
    return render_template('index.html')


@app.route('/api/task/create', methods=['POST'])
def create_task():
    """Cria e inicia execução de uma tarefa."""
    data = request.json
    task_text = data.get('task')
    
    if not task_text:
        return jsonify({'error': 'Task text is required'}), 400
    
    # Criar ID único
    task_id = str(uuid.uuid4())
    
    # Criar execução
    execution = TaskExecution(task_id, task_text)
    executions[task_id] = execution
    
    # Executar em thread separada
    def run_async():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(execution.execute())
        loop.close()
    
    thread = threading.Thread(target=run_async, daemon=True)
    thread.start()
    
    return jsonify({
        'task_id': task_id,
        'status': 'initializing'
    })


@app.route('/api/task/<task_id>/status')
def get_task_status(task_id):
    """Retorna status de uma tarefa."""
    execution = executions.get(task_id)
    if not execution:
        return jsonify({'error': 'Task not found'}), 404
    
    return jsonify({
        'task_id': task_id,
        'status': execution.status,
        'agents': execution.agents,
        'message_count': len(execution.messages),
        'artifact_count': len(execution.artifacts),
        'start_time': execution.start_time.isoformat(),
        'end_time': execution.end_time.isoformat() if execution.end_time else None
    })


@app.route('/api/task/<task_id>/messages')
def get_task_messages(task_id):
    """Retorna mensagens de uma tarefa."""
    execution = executions.get(task_id)
    if not execution:
        return jsonify({'error': 'Task not found'}), 404
    
    return jsonify({
        'messages': execution.messages
    })


@app.route('/api/task/<task_id>/artifacts')
def get_task_artifacts(task_id):
    """Retorna artefatos de uma tarefa."""
    execution = executions.get(task_id)
    if not execution:
        return jsonify({'error': 'Task not found'}), 404
    
    return jsonify({
        'artifacts': execution.artifacts
    })


@socketio.on('join_task')
def handle_join_task(data):
    """Cliente se junta a uma task room."""
    task_id = data.get('task_id')
    if task_id:
        from flask_socketio import join_room
        join_room(task_id)
        emit('joined', {'task_id': task_id})


@socketio.on('disconnect')
def handle_disconnect():
    """Cliente desconectou."""
    pass


if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)

