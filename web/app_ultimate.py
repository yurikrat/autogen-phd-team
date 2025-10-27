#!/usr/bin/env python3
"""
Interface Web para Ultimate Executor.
Simples, direto e funcional!
"""

import os
import sys
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit

# Adicionar path do projeto
sys.path.insert(0, str(Path(__file__).parent.parent))

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'ultimate-executor-secret')
socketio = SocketIO(app, cors_allowed_origins="*")

# Estado da execução
current_execution = {
    'running': False,
    'task': None,
    'output_dir': None,
    'files': [],
    'logs': []
}


@app.route('/')
def index():
    """Página principal."""
    return render_template('index_ultimate.html')


@app.route('/api/execute', methods=['POST'])
def execute_task():
    """Executa tarefa com Ultimate Executor."""
    
    if current_execution['running']:
        return jsonify({'error': 'Já existe uma execução em andamento'}), 400
    
    data = request.json
    task = data.get('task', '').strip()
    
    if not task:
        return jsonify({'error': 'Tarefa não pode ser vazia'}), 400
    
    # Iniciar execução em background
    socketio.start_background_task(run_executor, task)
    
    return jsonify({'status': 'started', 'task': task})


def run_executor(task: str):
    """Executa Ultimate Executor e envia updates via WebSocket."""
    
    current_execution['running'] = True
    current_execution['task'] = task
    current_execution['files'] = []
    current_execution['logs'] = []
    
    socketio.emit('execution_started', {'task': task})
    
    try:
        # Executar ultimate_executor.py
        script_path = Path(__file__).parent.parent / 'ultimate_executor.py'
        
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
                current_execution['logs'].append(line)
                socketio.emit('log', {'message': line})
                
                # Detectar arquivos criados
                if '✅' in line and 'bytes' in line:
                    # Extrair nome do arquivo
                    parts = line.split('✅')[1].strip().split('(')
                    if len(parts) >= 2:
                        filename = parts[0].strip()
                        size = parts[1].split(')')[0].strip()
                        current_execution['files'].append({
                            'filename': filename,
                            'size': size
                        })
                        socketio.emit('file_created', {
                            'filename': filename,
                            'size': size
                        })
                
                # Detectar output directory
                if 'Output:' in line or 'Localização:' in line:
                    try:
                        output_dir = line.split(':')[1].strip()
                        current_execution['output_dir'] = output_dir
                        socketio.emit('output_dir', {'path': output_dir})
                    except:
                        pass
        
        process.wait()
        
        if process.returncode == 0:
            socketio.emit('execution_completed', {
                'status': 'success',
                'files': current_execution['files'],
                'output_dir': current_execution['output_dir']
            })
        else:
            socketio.emit('execution_completed', {
                'status': 'error',
                'message': 'Execução falhou'
            })
    
    except Exception as e:
        socketio.emit('execution_error', {'error': str(e)})
    
    finally:
        current_execution['running'] = False


@app.route('/api/status', methods=['GET'])
def get_status():
    """Retorna status da execução atual."""
    return jsonify({
        'running': current_execution['running'],
        'task': current_execution['task'],
        'files': current_execution['files'],
        'output_dir': current_execution['output_dir']
    })


@app.route('/api/runs', methods=['GET'])
def list_runs():
    """Lista runs anteriores."""
    runs_dir = Path(__file__).parent.parent / 'runs'
    
    if not runs_dir.exists():
        return jsonify({'runs': []})
    
    runs = []
    for run_dir in sorted(runs_dir.iterdir(), reverse=True):
        if run_dir.is_dir():
            files = list(run_dir.glob('*'))
            runs.append({
                'name': run_dir.name,
                'path': str(run_dir),
                'files': len(files),
                'timestamp': run_dir.stat().st_mtime
            })
    
    return jsonify({'runs': runs[:20]})  # Últimas 20 runs


if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    print(f"\n🚀 Ultimate Executor Web Interface")
    print(f"   Acesse: http://localhost:{port}\n")
    socketio.run(app, host='0.0.0.0', port=port, debug=False)

