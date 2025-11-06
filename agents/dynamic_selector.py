#!/usr/bin/env python3
"""
Dynamic Selector - Seleção dinâmica de agentes baseada em palavras-chave.

O sistema analisa a task description e ativa agentes relevantes automaticamente.

Exemplo:
- Task "API FastAPI JWT" → ativa Backend_Dev + IAM_Engineer
- Task "Dashboard analytics" → ativa BI_Analyst + Data_Scientist + Frontend_Dev
"""

import re
from typing import List, Dict, Set
from agents.all_agents import ALL_AGENTS, get_core_agents


# Mapeamento de palavras-chave para agentes
KEYWORD_TO_AGENTS = {
    # Backend & APIs
    'api': ['Backend_Dev'],
    'rest': ['Backend_Dev'],
    'graphql': ['Backend_Dev'],
    'fastapi': ['Backend_Dev'],
    'flask': ['Backend_Dev'],
    'django': ['Backend_Dev'],
    'backend': ['Backend_Dev'],
    'servidor': ['Backend_Dev'],
    'endpoint': ['Backend_Dev'],
    
    # Frontend
    'frontend': ['Frontend_Dev', 'UX_UI_Designer'],
    'react': ['Frontend_Dev'],
    'vue': ['Frontend_Dev'],
    'next': ['Frontend_Dev'],
    'interface': ['Frontend_Dev', 'UX_UI_Designer'],
    'ui': ['Frontend_Dev', 'UX_UI_Designer'],
    'ux': ['UX_UI_Designer'],
    'design': ['UX_UI_Designer'],
    'wireframe': ['UX_UI_Designer'],
    'protótipo': ['UX_UI_Designer'],
    
    # Mobile
    'mobile': ['Mobile_Dev'],
    'app': ['Mobile_Dev'],
    'ios': ['Mobile_Dev'],
    'android': ['Mobile_Dev'],
    'flutter': ['Mobile_Dev'],
    'react native': ['Mobile_Dev'],
    
    # Banco de Dados
    'database': ['DBA_Engineer'],
    'banco': ['DBA_Engineer'],
    'sql': ['DBA_Engineer'],
    'postgres': ['DBA_Engineer'],
    'mysql': ['DBA_Engineer'],
    'mongodb': ['DBA_Engineer'],
    'redis': ['DBA_Engineer'],
    'schema': ['DBA_Engineer'],
    'migration': ['DBA_Engineer'],
    
    # Dados & Analytics
    'analytics': ['BI_Analyst', 'Data_Scientist'],
    'dashboard': ['BI_Analyst', 'Frontend_Dev'],
    'kpi': ['BI_Analyst'],
    'visualização': ['BI_Analyst'],
    'etl': ['Data_Engineer'],
    'pipeline': ['Data_Engineer'],
    'data lake': ['Data_Engineer'],
    'warehouse': ['Data_Engineer'],
    'machine learning': ['Data_Scientist', 'ML_Engineer'],
    'ml': ['Data_Scientist', 'ML_Engineer'],
    'modelo': ['Data_Scientist', 'ML_Engineer'],
    'predição': ['Data_Scientist'],
    'classificação': ['Data_Scientist'],
    
    # Segurança & Autenticação
    'segurança': ['AppSec', 'SecOps'],
    'security': ['AppSec', 'SecOps'],
    'auth': ['IAM_Engineer'],
    'autenticação': ['IAM_Engineer'],
    'jwt': ['IAM_Engineer', 'Backend_Dev'],
    'oauth': ['IAM_Engineer'],
    'sso': ['IAM_Engineer'],
    'login': ['IAM_Engineer', 'Backend_Dev'],
    'permissão': ['IAM_Engineer'],
    'rbac': ['IAM_Engineer'],
    'owasp': ['AppSec'],
    'vulnerabilidade': ['AppSec'],
    'pentest': ['AppSec'],
    'lgpd': ['Compliance_Officer'],
    'gdpr': ['Compliance_Officer'],
    
    # DevOps & Infra
    'docker': ['DevOps_SRE'],
    'kubernetes': ['DevOps_SRE', 'Cloud_Architect'],
    'k8s': ['DevOps_SRE', 'Cloud_Architect'],
    'ci/cd': ['DevOps_SRE'],
    'pipeline': ['DevOps_SRE'],
    'deploy': ['DevOps_SRE', 'Release_Manager'],
    'terraform': ['DevOps_SRE', 'Cloud_Architect'],
    'ansible': ['DevOps_SRE', 'SysAdmin'],
    'cloud': ['Cloud_Architect'],
    'aws': ['Cloud_Architect'],
    'azure': ['Cloud_Architect'],
    'gcp': ['Cloud_Architect'],
    'serverless': ['Cloud_Architect'],
    'lambda': ['Cloud_Architect'],
    
    # Monitoramento
    'monitoramento': ['Monitoring_Analyst'],
    'monitoring': ['Monitoring_Analyst'],
    'grafana': ['Monitoring_Analyst'],
    'prometheus': ['Monitoring_Analyst'],
    'datadog': ['Monitoring_Analyst'],
    'logs': ['Monitoring_Analyst'],
    'métricas': ['Monitoring_Analyst'],
    'alertas': ['Monitoring_Analyst'],
    
    # Testes & Qualidade
    'teste': ['QA_Engineer'],
    'test': ['QA_Engineer'],
    'pytest': ['QA_Engineer'],
    'unittest': ['QA_Engineer'],
    'qa': ['QA_Engineer'],
    'qualidade': ['QA_Engineer'],
    'performance': ['Performance_Engineer'],
    'benchmark': ['Performance_Engineer'],
    'otimização': ['Performance_Engineer'],
    'latência': ['Performance_Engineer'],
    
    # Integração
    'integração': ['Integration_Engineer'],
    'webhook': ['Integration_Engineer'],
    'api externa': ['Integration_Engineer'],
    'terceiros': ['Integration_Engineer'],
    
    # Gestão
    'requisitos': ['Business_Analyst', 'Product_Owner'],
    'user story': ['Product_Owner'],
    'backlog': ['Product_Owner'],
    'roadmap': ['Product_Owner', 'Project_Manager'],
    'release': ['Release_Manager'],
    
    # AI & Prompts
    'prompt': ['Prompt_Engineer'],
    'llm': ['Prompt_Engineer', 'AI_Security_Officer'],
    'gpt': ['Prompt_Engineer'],
    'ai': ['Prompt_Engineer', 'AI_Security_Officer'],
}


def extract_keywords(task_description: str) -> Set[str]:
    """Extrai palavras-chave da task description."""
    # Converter para minúsculas
    text = task_description.lower()
    
    # Encontrar todas as palavras-chave presentes
    found_keywords = set()
    
    for keyword in KEYWORD_TO_AGENTS.keys():
        # Usar regex para encontrar palavra completa
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, text):
            found_keywords.add(keyword)
    
    return found_keywords


def select_agents_by_keywords(task_description: str) -> Dict[str, List[str]]:
    """
    Seleciona agentes baseado em palavras-chave da task.
    
    Returns:
        Dict com 'core' (sempre presentes) e 'selected' (selecionados dinamicamente)
    """
    # Extrair palavras-chave
    keywords = extract_keywords(task_description)
    
    # Agentes selecionados
    selected_agent_names = set()
    
    # Mapear keywords para agentes
    keyword_matches = {}
    for keyword in keywords:
        agents = KEYWORD_TO_AGENTS.get(keyword, [])
        keyword_matches[keyword] = agents
        selected_agent_names.update(agents)
    
    # Sempre incluir QA e Code_Validator
    selected_agent_names.add('QA_Engineer')
    selected_agent_names.add('Code_Validator')
    
    return {
        'core': list(ALL_AGENTS['core'].keys()),  # Sempre presentes
        'selected': sorted(list(selected_agent_names)),
        'keywords_found': sorted(list(keywords)),
        'keyword_matches': keyword_matches
    }


def get_selected_agents_instances(task_description: str) -> Dict:
    """
    Retorna instâncias dos agentes selecionados.
    
    Returns:
        Dict com agentes do núcleo e selecionados
    """
    selection = select_agents_by_keywords(task_description)
    
    # Criar instâncias dos agentes do núcleo
    core_agents = get_core_agents()
    
    # Criar instâncias dos agentes selecionados
    selected_agents = {}
    for agent_name in selection['selected']:
        # Encontrar agente em todas as categorias
        for category, agents in ALL_AGENTS.items():
            if agent_name in agents:
                selected_agents[agent_name] = agents[agent_name]()
                break
    
    return {
        'core': core_agents,
        'selected': selected_agents,
        'selection_info': selection
    }


def print_selection_summary(task_description: str):
    """Imprime resumo da seleção de agentes."""
    selection = select_agents_by_keywords(task_description)
    
    print("\n" + "=" * 80)
    print("🎯 SELEÇÃO DINÂMICA DE AGENTES")
    print("=" * 80)
    print(f"\n📋 Task: {task_description}\n")
    
    # Palavras-chave encontradas
    print(f"🔍 Palavras-chave encontradas ({len(selection['keywords_found'])}):")
    for keyword in selection['keywords_found']:
        agents = selection['keyword_matches'].get(keyword, [])
        print(f"   • {keyword} → {', '.join(agents)}")
    
    print(f"\n👥 Agentes selecionados:")
    
    # Núcleo
    print(f"\n   📌 NÚCLEO ({len(selection['core'])} agentes - sempre presentes):")
    for agent in selection['core']:
        print(f"      • {agent}")
    
    # Selecionados
    print(f"\n   ⭐ SELECIONADOS ({len(selection['selected'])} agentes):")
    for agent in selection['selected']:
        print(f"      • {agent}")
    
    total = len(selection['core']) + len(selection['selected'])
    print(f"\n📊 Total de agentes ativos: {total}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    # Testes
    test_tasks = [
        "Criar API REST com FastAPI usando JWT para autenticação",
        "Dashboard analytics com visualizações de KPIs em React",
        "Pipeline ETL para data lake com Airflow",
        "App mobile iOS/Android com React Native",
        "Deploy com Docker e Kubernetes na AWS",
        "Sistema de monitoramento com Grafana e Prometheus",
        "Modelo de machine learning para classificação",
        "Integração com API externa via webhook"
    ]
    
    for task in test_tasks:
        print_selection_summary(task)
        print("\n")

