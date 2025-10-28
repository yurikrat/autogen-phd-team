#!/usr/bin/env python3
"""
Interface Web para Crew Advanced.
Mostra tarefas separadas por agente, artefatos organizados e colaboração em tempo real.
"""

import os
import sys
import json
import subprocess
import threading
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit

sys.path.insert(0, str(Path(__file__).parent.parent))

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'crew-advanced-secret')
socketio = SocketIO(app, cors_allowed_origins="*")

# Estado da execução
execution_state = {
    'running': False,
    'task': None,
    'output_dir': None,
    'current_agent': None,
    'current_task': None,
    'agents_progress': {},
    'artifacts_by_agent': {},
    'logs': []
}


@app.route('/')
def index():
    """Página principal."""
    return render_template('index_crew.html')


@app.route('/api/execute', methods=['POST'])
def execute_task():
    """Executa tarefa com Crew Advanced."""
    
    if execution_state['running']:
        return jsonify({'error': 'Já existe uma execução em andamento'}), 400
    
    data = request.json
    task = data.get('task', '').strip()
    
    if not task:
        return jsonify({'error': 'Tarefa não pode ser vazia'}), 400
    
    # Resetar estado
    execution_state['running'] = True
    execution_state['task'] = task
    execution_state['agents_progress'] = {
        'Architect': {'status': 'pending', 'artifacts': []},
        'Backend_Dev': {'status': 'pending', 'artifacts': []},
        'QA_Engineer': {'status': 'pending', 'artifacts': []},
        'Security_Expert': {'status': 'pending', 'artifacts': []},
        'Tech_Writer': {'status': 'pending', 'artifacts': []}
    }
    execution_state['artifacts_by_agent'] = {}
    execution_state['logs'] = []
    
    # Iniciar execução em background
    socketio.start_background_task(run_crew, task)
    
    return jsonify({'status': 'started', 'task': task})


def parse_log_line(line: str):
    """Parse linha de log para extrair informações."""
    
    # Detectar agente atual
    if 'Agent:' in line:
        for agent in ['Software Architect', 'Backend Developer', 'QA Engineer', 'Security Expert', 'Technical Writer']:
            if agent in line:
                agent_key = agent.replace(' ', '_')
                execution_state['current_agent'] = agent_key
                execution_state['agents_progress'][agent_key]['status'] = 'running'
                socketio.emit('agent_started', {
                    'agent': agent_key,
                    'name': agent
                })
                break
    
    # Detectar artefato criado
    if '✅ Artefato salvo:' in line:
        try:
            # Extrair path e tamanho
            parts = line.split('✅ Artefato salvo:')[1].strip()
            filepath = parts.split('(')[0].strip()
            size = parts.split('(')[1].split(')')[0].strip()
            
            filename = Path(filepath).name
            agent_dir = Path(filepath).parent.name
            
            # Mapear diretório para agente
            agent_map = {
                'architect': 'Architect',
                'backend_dev': 'Backend_Dev',
                'qa_engineer': 'QA_Engineer',
                'security_expert': 'Security_Expert',
                'tech_writer': 'Tech_Writer'
            }
            
            agent_key = agent_map.get(agent_dir, 'Unknown')
            
            artifact = {
                'filename': filename,
                'size': size,
                'path': filepath,
                'timestamp': datetime.now().isoformat()
            }
            
            if agent_key not in execution_state['artifacts_by_agent']:
                execution_state['artifacts_by_agent'][agent_key] = []
            
            execution_state['artifacts_by_agent'][agent_key].append(artifact)
            execution_state['agents_progress'][agent_key]['artifacts'].append(artifact)
            
            socketio.emit('artifact_created', {
                'agent': agent_key,
                'artifact': artifact
            })
        except:
            pass
    
    # Detectar task concluída
    if 'Task completed' in line or 'expected_output' in line.lower():
        if execution_state['current_agent']:
            execution_state['agents_progress'][execution_state['current_agent']]['status'] = 'completed'
            socketio.emit('agent_completed', {
                'agent': execution_state['current_agent']
            })


def run_crew(task: str):
    """Executa Crew Advanced e envia updates via WebSocket."""
    
    socketio.emit('execution_started', {
        'task': task,
        'agents': list(execution_state['agents_progress'].keys())
    })
    
    try:
        script_path = Path(__file__).parent.parent / 'crew_advanced.py'
        
        process = subprocess.Popen(
            ['python', str(script_path), task],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Ler output linha por linha
        for line in iter(process.stdout.readline, ''):
            if line:
                line = line.rstrip()
                execution_state['logs'].append(line)
                
                # Parse para extrair informações
                parse_log_line(line)
                
                # Enviar log
                socketio.emit('log', {'message': line})
                
                # Detectar output directory
                if 'Output:' in line or 'Localização:' in line:
                    try:
                        output_dir = line.split(':')[1].strip()
                        execution_state['output_dir'] = output_dir
                        socketio.emit('output_dir', {'path': output_dir})
                    except:
                        pass
        
        process.wait()
        
        # Carregar summary se existir
        if execution_state['output_dir']:
            summary_path = Path(execution_state['output_dir']) / 'SUMMARY.json'
            if summary_path.exists():
                with open(summary_path, 'r') as f:
                    summary = json.load(f)
                    socketio.emit('summary', summary)
        
        if process.returncode == 0:
            socketio.emit('execution_completed', {
                'status': 'success',
                'artifacts_by_agent': execution_state['artifacts_by_agent'],
                'output_dir': execution_state['output_dir']
            })
        else:
            socketio.emit('execution_completed', {
                'status': 'error',
                'message': 'Execução falhou'
            })
    
    except Exception as e:
        socketio.emit('execution_error', {'error': str(e)})
    
    finally:
        execution_state['running'] = False


@app.route('/api/status', methods=['GET'])
def get_status():
    """Retorna status da execução atual."""
    return jsonify({
        'running': execution_state['running'],
        'task': execution_state['task'],
        'current_agent': execution_state['current_agent'],
        'agents_progress': execution_state['agents_progress'],
        'artifacts_by_agent': execution_state['artifacts_by_agent'],
        'output_dir': execution_state['output_dir']
    })


@app.route('/api/artifacts/<agent>', methods=['GET'])
def get_agent_artifacts(agent):
    """Retorna artefatos de um agente específico."""
    artifacts = execution_state['artifacts_by_agent'].get(agent, [])
    return jsonify({'agent': agent, 'artifacts': artifacts})


if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    print(f"\n🎼 Crew Advanced Web Interface")
    print(f"   Acesse: http://localhost:{port}\n")
    socketio.run(app, host='0.0.0.0', port=port, debug=False)

