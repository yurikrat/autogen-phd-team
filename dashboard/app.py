"""
Dashboard Web em Tempo Real para visualização da orquestra de agentes.
"""

from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import json
import os
from pathlib import Path
from datetime import datetime
import threading
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'autogen-phd-team-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# Estado global do dashboard
dashboard_state = {
    "agents": {},
    "messages": [],
    "artifacts": [],
    "interactions": [],
    "metrics": {
        "total_messages": 0,
        "total_artifacts": 0,
        "active_agents": 0,
        "challenges_issued": 0,
        "improvements_made": 0,
    },
    "run_dir": None,
    "status": "idle",  # idle, running, completed, error
}


def update_dashboard(event_type: str, data: dict):
    """
    Atualiza o estado do dashboard e notifica clientes via WebSocket.
    
    Args:
        event_type: Tipo de evento (message, artifact, metric, etc.)
        data: Dados do evento
    """
    global dashboard_state
    
    if event_type == "message":
        dashboard_state["messages"].append(data)
        dashboard_state["metrics"]["total_messages"] += 1
        
        # Registrar interação entre agentes
        if "source" in data and "target" in data:
            dashboard_state["interactions"].append({
                "from": data["source"],
                "to": data["target"],
                "timestamp": data.get("timestamp", datetime.now().isoformat())
            })
        
        # Atualizar status do agente
        if "source" in data:
            agent_name = data["source"]
            if agent_name not in dashboard_state["agents"]:
                dashboard_state["agents"][agent_name] = {
                    "name": agent_name,
                    "status": "active",
                    "messages_sent": 0,
                    "last_activity": None,
                }
            
            dashboard_state["agents"][agent_name]["messages_sent"] += 1
            dashboard_state["agents"][agent_name]["last_activity"] = data.get("timestamp")
            dashboard_state["agents"][agent_name]["status"] = "active"
    
    elif event_type == "artifact":
        dashboard_state["artifacts"].append(data)
        dashboard_state["metrics"]["total_artifacts"] += 1
    
    elif event_type == "metric":
        dashboard_state["metrics"].update(data)
    
    elif event_type == "status":
        dashboard_state["status"] = data.get("status", "idle")
        if "run_dir" in data:
            dashboard_state["run_dir"] = data["run_dir"]
    
    elif event_type == "challenge":
        dashboard_state["metrics"]["challenges_issued"] += 1
    
    elif event_type == "improvement":
        dashboard_state["metrics"]["improvements_made"] += 1
    
    # Atualizar contagem de agentes ativos
    dashboard_state["metrics"]["active_agents"] = len([
        a for a in dashboard_state["agents"].values()
        if a["status"] == "active"
    ])
    
    # Notificar clientes via WebSocket
    socketio.emit('dashboard_update', {
        'event_type': event_type,
        'data': data,
        'state': dashboard_state
    })


@app.route('/')
def index():
    """Página principal do dashboard."""
    return render_template('dashboard.html')


@app.route('/api/state')
def get_state():
    """Retorna o estado atual do dashboard."""
    return jsonify(dashboard_state)


@app.route('/api/artifacts')
def get_artifacts():
    """Retorna lista de artefatos."""
    return jsonify(dashboard_state["artifacts"])


@app.route('/api/artifact/<path:filepath>')
def get_artifact_content(filepath):
    """Retorna o conteúdo de um artefato."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({"status": "ok", "content": content})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 404


@socketio.on('connect')
def handle_connect():
    """Cliente conectado ao WebSocket."""
    emit('dashboard_update', {
        'event_type': 'init',
        'data': {},
        'state': dashboard_state
    })


@socketio.on('disconnect')
def handle_disconnect():
    """Cliente desconectado do WebSocket."""
    pass


def run_dashboard(host='0.0.0.0', port=5000):
    """Inicia o servidor do dashboard."""
    socketio.run(app, host=host, port=port, debug=False, allow_unsafe_werkzeug=True)


def start_dashboard_thread(host='0.0.0.0', port=5000):
    """Inicia o dashboard em uma thread separada."""
    thread = threading.Thread(
        target=run_dashboard,
        args=(host, port),
        daemon=True
    )
    thread.start()
    return thread


# Função auxiliar para ser importada pelo team_runtime
def emit_event(event_type: str, data: dict):
    """
    Emite um evento para o dashboard.
    Pode ser chamada de qualquer lugar do código.
    """
    update_dashboard(event_type, data)


if __name__ == '__main__':
    run_dashboard()

