"""
Routing: heurística de seleção dinâmica de papéis com base em palavras-chave da task.
"""

from typing import List

# Núcleo sempre presente
CORE_ALWAYS = ["AI_Orchestrator", "Project_Manager", "Tech_Architect", "Finalizer"]

# Palavras-chave para ativação de papéis adicionais (português minúsculo)
KEYWORDS = {
    "Backend_Dev": [
        "api", "rest", "graphql", "backend", "servidor", "microsserviço", "microservice",
        "fastapi", "flask", "django", "express", "node", "spring", "endpoint",
        "serviço", "worker", "job", "queue", "fila", "kafka", "rabbitmq"
    ],
    "Frontend_Dev": [
        "frontend", "front-end", "ui", "interface", "react", "vue", "angular",
        "componente", "página", "web app", "spa", "ssr", "next", "nuxt",
        "html", "css", "javascript", "typescript", "tailwind", "bootstrap"
    ],
    "Mobile_Dev": [
        "mobile", "app", "ios", "android", "swift", "kotlin", "react native",
        "flutter", "xamarin", "cordova", "ionic", "nativo", "aplicativo móvel"
    ],
    "Integration_Engineer": [
        "integração", "integration", "webhook", "api externa", "third-party",
        "connector", "adapter", "middleware", "etl", "sync", "sincronização"
    ],
    "DBA_Engineer": [
        "banco", "database", "sql", "postgres", "mysql", "oracle", "mongodb",
        "redis", "cassandra", "dynamodb", "schema", "índice", "query",
        "otimização de banco", "migração", "backup", "replicação"
    ],
    "Data_Engineer": [
        "pipeline", "etl", "elt", "airflow", "spark", "hadoop", "dbt",
        "data lake", "data warehouse", "bigquery", "redshift", "snowflake",
        "ingestão", "transformação", "processamento de dados"
    ],
    "Data_Scientist": [
        "machine learning", "ml", "modelo", "predição", "forecasting",
        "estatística", "análise", "clustering", "classificação", "regressão",
        "scikit-learn", "tensorflow", "pytorch", "notebook", "jupyter"
    ],
    "BI_Analyst": [
        "dashboard", "bi", "business intelligence", "kpi", "métrica",
        "relatório", "visualização", "metabase", "tableau", "power bi",
        "looker", "superset", "análise de negócio"
    ],
    "ML_Engineer": [
        "mlops", "deploy de modelo", "inferência", "treinamento",
        "versionamento de modelo", "mlflow", "kubeflow", "sagemaker",
        "model serving", "onnx", "torchserve", "drift"
    ],
    "DevOps_SRE": [
        "devops", "sre", "ci/cd", "pipeline", "jenkins", "github actions",
        "gitlab ci", "terraform", "ansible", "kubernetes", "k8s", "helm",
        "docker", "container", "observabilidade", "monitoring", "slo", "sla"
    ],
    "Cloud_Architect": [
        "cloud", "aws", "azure", "gcp", "nuvem", "serverless", "lambda",
        "s3", "ec2", "rds", "cloudformation", "arquitetura cloud",
        "multi-cloud", "hybrid cloud"
    ],
    "Network_Admin": [
        "rede", "network", "vpc", "subnet", "firewall", "load balancer",
        "dns", "cdn", "vpn", "peering", "routing", "segmentação de rede"
    ],
    "SysAdmin": [
        "servidor", "linux", "ubuntu", "centos", "windows server",
        "administração", "sysadmin", "script", "bash", "powershell",
        "automação de servidor", "patch", "update"
    ],
    "SecOps": [
        "secops", "segurança", "security", "siem", "ids", "ips",
        "incident response", "threat", "vulnerabilidade", "waf",
        "ddos", "monitoramento de segurança"
    ],
    "AppSec": [
        "appsec", "owasp", "code review", "sast", "dast", "sca",
        "injeção", "xss", "csrf", "ssrf", "secure coding",
        "segurança de aplicação"
    ],
    "Compliance_Officer": [
        "compliance", "conformidade", "lgpd", "gdpr", "hipaa", "pci-dss",
        "sox", "auditoria", "governança", "privacidade", "dpia",
        "regulamentação", "política"
    ],
    "IAM_Engineer": [
        "iam", "identidade", "autenticação", "autorização", "oauth",
        "oidc", "saml", "sso", "mfa", "rbac", "abac", "least privilege",
        "gestão de acesso", "secrets management"
    ],
    "QA_Engineer": [
        "qa", "teste", "testing", "qualidade", "test automation",
        "selenium", "cypress", "jest", "pytest", "unittest",
        "cobertura", "bug", "validação"
    ],
    "Performance_Engineer": [
        "performance", "otimização", "benchmark", "carga", "stress",
        "jmeter", "gatling", "k6", "latência", "throughput",
        "escalabilidade", "gargalo"
    ],
    "Release_Manager": [
        "release", "deploy", "deployment", "rollout", "rollback",
        "blue-green", "canary", "feature flag", "hotfix", "patch",
        "release notes", "changelog"
    ],
    "UX_UI_Designer": [
        "ux", "ui", "design", "interface", "wireframe", "mockup",
        "protótipo", "figma", "sketch", "adobe xd", "design system",
        "usabilidade", "acessibilidade", "wcag"
    ],
    "Product_Owner": [
        "product owner", "po", "produto", "backlog", "user story",
        "roadmap", "okr", "priorização", "visão de produto",
        "critérios de aceite"
    ],
    "Business_Analyst": [
        "business analyst", "ba", "requisitos", "processo de negócio",
        "bpmn", "caso de uso", "análise de negócio", "stakeholder",
        "levantamento de requisitos"
    ],
    "ITSM_Manager": [
        "itsm", "itil", "incident", "problem", "change management",
        "service desk", "sla", "cmdb", "knowledge base", "cab"
    ],
    "Support_Engineer": [
        "suporte", "support", "ticket", "troubleshooting", "l1", "l2", "l3",
        "helpdesk", "atendimento", "resolução de problemas"
    ],
    "Monitoring_Analyst": [
        "monitoring", "observabilidade", "grafana", "datadog", "new relic",
        "prometheus", "alert", "dashboard", "métrica", "log", "trace"
    ],
    "Prompt_Engineer": [
        "prompt", "llm", "gpt", "claude", "gemini", "openai",
        "prompt engineering", "few-shot", "chain-of-thought", "react",
        "engenharia de prompt"
    ],
    "AI_Security_Officer": [
        "ai security", "adversarial", "model security", "data poisoning",
        "model inversion", "fairness", "bias", "viés", "responsible ai",
        "segurança de ia"
    ],
}


def select_roles(task_text: str) -> List[str]:
    """
    Seleciona papéis dinamicamente com base em palavras-chave da task.
    
    Args:
        task_text: Texto da task fornecida pelo usuário
    
    Returns:
        Lista de nomes de papéis a serem ativados
    """
    task_lower = task_text.lower()
    selected = set(CORE_ALWAYS)  # Núcleo sempre presente
    
    # Varrer palavras-chave
    for role, keywords in KEYWORDS.items():
        for keyword in keywords:
            if keyword in task_lower:
                selected.add(role)
                break  # Basta uma palavra-chave bater
    
    # Fallback: se nenhum papel adicional foi selecionado, incluir Backend_Dev
    if len(selected) == len(CORE_ALWAYS):
        selected.add("Backend_Dev")
    
    return sorted(list(selected))

