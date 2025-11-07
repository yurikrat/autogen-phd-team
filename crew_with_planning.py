#!/usr/bin/env python3
"""
CrewAI com Planning + Hierarchical Process + LLM Router V3.

Implementa decomposição automática de tasks complexas com:
- Planning: AgentPlanner decompõe tasks em steps
- Hierarchical: Manager Agent coordena e delega
- LLM Router V3: Circuit Breaker + Adaptive Timeout
- Agentes Granulares: 10 agentes especializados

Solução para travamentos em tasks complexas.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool

# Carregar variáveis de ambiente
load_dotenv()

# Importar LLM Router V3
sys.path.insert(0, str(Path(__file__).parent))
from utils.llm_router import get_llm_router


def create_llm(temperature=0.7):
    """Cria LLM com LLM Router V3 (Circuit Breaker + Adaptive Timeout)."""
    return get_llm_router(
        model="deepseek-chat",
        temperature=temperature,
        cooldown_seconds=60,
        max_retries=3,
        base_timeout=60,
        auto_complexity_detection=True,
        enable_circuit_breaker=True
    )


# ============================================================================
# AGENTES GRANULARES (Especializados)
# ============================================================================

def create_technical_planner():
    """Planner - Analisa requisitos e cria plano detalhado."""
    return Agent(
        role="Technical Planner",
        goal="Analyze requirements and create detailed step-by-step implementation plan",
        backstory="""You are an expert technical planner with 15+ years of experience 
        breaking down complex software projects into manageable tasks.
        
        You excel at:
        - Identifying all components needed
        - Creating logical task sequences
        - Estimating complexity and effort
        - Spotting potential risks early
        - Defining clear acceptance criteria
        
        You create plans that teams can execute efficiently.""",
        verbose=True,
        allow_delegation=False,
        llm=create_llm(0.8)
    )


def create_software_architect():
    """Architect - Define arquitetura e estrutura."""
    return Agent(
        role="Software Architect",
        goal="Design system architecture, data models, and technical specifications",
        backstory="""You are a senior software architect with deep expertise in 
        scalable, maintainable system design.
        
        You excel at:
        - Designing clean architectures
        - Defining data models and schemas
        - Choosing appropriate technologies
        - Establishing coding standards
        - Creating technical documentation
        
        You ensure systems are built on solid foundations.""",
        verbose=True,
        allow_delegation=False,
        llm=create_llm(0.7)
    )


def create_backend_developer():
    """Backend Developer - Implementa backend."""
    return Agent(
        role="Backend Developer",
        goal="Implement robust backend services, APIs, and business logic",
        backstory="""You are a senior backend developer specializing in Python, 
        FastAPI, and modern backend architectures.
        
        You excel at:
        - Building RESTful APIs
        - Implementing authentication (JWT, OAuth)
        - Database design and queries
        - Caching strategies (Redis)
        - Async task processing (Celery)
        - WebSocket real-time features
        
        You write clean, efficient, testable backend code.""",
        verbose=True,
        allow_delegation=False,
        llm=create_llm(0.7)
    )


def create_database_engineer():
    """Database Engineer - Migrations, models, schemas."""
    return Agent(
        role="Database Engineer",
        goal="Design database schemas, create migrations, and optimize queries",
        backstory="""You are a database specialist with expertise in PostgreSQL, 
        SQLAlchemy, and Alembic migrations.
        
        You excel at:
        - Designing normalized schemas
        - Creating efficient migrations
        - Optimizing query performance
        - Implementing indexes
        - Multi-tenancy data isolation
        
        You ensure data integrity and performance.""",
        verbose=True,
        allow_delegation=False,
        llm=create_llm(0.7)
    )


def create_devops_engineer():
    """DevOps Engineer - Docker, CI/CD, infraestrutura."""
    return Agent(
        role="DevOps Engineer",
        goal="Setup infrastructure, containerization, CI/CD, and observability",
        backstory="""You are a DevOps expert specializing in Docker, Kubernetes, 
        and modern deployment pipelines.
        
        You excel at:
        - Creating optimized Dockerfiles
        - Orchestrating with docker-compose
        - Building CI/CD pipelines (GitHub Actions)
        - Setting up monitoring (Prometheus, Grafana)
        - Implementing OpenTelemetry
        - Infrastructure as Code
        
        You make deployments reliable and observable.""",
        verbose=True,
        allow_delegation=False,
        llm=create_llm(0.7)
    )


def create_qa_engineer():
    """QA Engineer - Testes unitários, integração, cobertura."""
    return Agent(
        role="QA Engineer",
        goal="Create comprehensive test suites with >=85% coverage",
        backstory="""You are a quality assurance specialist with expertise in 
        pytest, test automation, and TDD.
        
        You excel at:
        - Writing unit tests (pytest)
        - Integration testing
        - API testing
        - Test fixtures and mocks
        - Coverage analysis
        - Performance testing
        
        You ensure code quality through rigorous testing.""",
        verbose=True,
        allow_delegation=False,
        llm=create_llm(0.7)
    )


def create_security_engineer():
    """Security Engineer - Segurança, RBAC, audit."""
    return Agent(
        role="Security Engineer",
        goal="Implement security best practices, RBAC, and audit logging",
        backstory="""You are a security specialist focused on application security 
        and compliance.
        
        You excel at:
        - Implementing RBAC (Role-Based Access Control)
        - JWT token security
        - Input validation and sanitization
        - Audit logging
        - Rate limiting
        - Security headers
        
        You protect systems from vulnerabilities.""",
        verbose=True,
        allow_delegation=False,
        llm=create_llm(0.7)
    )


def create_documentation_specialist():
    """Documentation Specialist - README, docs, comentários."""
    return Agent(
        role="Documentation Specialist",
        goal="Create clear, comprehensive documentation for developers and users",
        backstory="""You are a technical writer who makes complex systems 
        understandable.
        
        You excel at:
        - Writing clear README files
        - Creating API documentation
        - Architecture diagrams
        - Setup instructions
        - Usage examples
        - Inline code comments
        
        You make codebases accessible to everyone.""",
        verbose=True,
        allow_delegation=False,
        llm=create_llm(0.7)
    )


def create_code_validator():
    """Code Validator - Valida imports, dependências, completude."""
    return Agent(
        role="Code Validator",
        goal="Validate code completeness, imports, dependencies, and best practices",
        backstory="""You are a code quality expert who ensures nothing is missing.
        
        You excel at:
        - Checking all imports exist
        - Validating dependencies
        - Ensuring file completeness
        - Verifying cross-references
        - Checking code standards
        - Spotting potential bugs
        
        You are the final quality gate.""",
        verbose=True,
        allow_delegation=False,
        llm=create_llm(0.7)
    )


def create_packaging_specialist():
    """Packaging Specialist - MANIFEST, ZIP, entrega final."""
    return Agent(
        role="Packaging Specialist",
        goal="Package deliverables, create manifests, and prepare final artifacts",
        backstory="""You are a release engineer who prepares perfect deliverables.
        
        You excel at:
        - Creating MANIFEST.md files
        - Packaging projects (ZIP)
        - Organizing deliverables
        - Final checklists
        - Release notes
        
        You ensure clean, professional deliveries.""",
        verbose=True,
        allow_delegation=False,
        llm=create_llm(0.7)
    )


# ============================================================================
# MANAGER AGENT (Coordenador Hierárquico)
# ============================================================================

def create_project_manager():
    """Project Manager - Coordena todo o workflow hierárquico."""
    return Agent(
        role="Project Manager",
        goal="Coordinate team, delegate tasks, validate results, and ensure project success",
        backstory="""You are an experienced project manager who leads technical teams 
        to deliver complex projects on time and with high quality.
        
        You excel at:
        - Understanding project requirements
        - Breaking down work into phases
        - Delegating to the right specialists
        - Tracking progress
        - Validating deliverables
        - Resolving blockers
        - Ensuring nothing is forgotten
        
        You are the orchestrator who makes everything come together.""",
        verbose=True,
        allow_delegation=True,  # ← Permite delegação
        llm=create_llm(0.8)
    )


# ============================================================================
# CREW COM PLANNING + HIERARCHICAL
# ============================================================================

def create_crew_with_planning(task_description: str, enable_memory: bool = False, embedder_config: dict = None):
    """
    Cria Crew com Planning + Hierarchical Process.
    
    Features:
    - Planning: AgentPlanner decompõe task automaticamente
    - Hierarchical: Manager coordena e delega
    - LLM Router V3: Circuit Breaker + Adaptive Timeout
    - 10 Agentes Granulares: Especializados
    - Memory (opcional): Short-term, Long-term, Entity
    
    Args:
        task_description: Descrição da task complexa
        enable_memory: Habilitar memory (requer embedder válido). Default: False
        embedder_config: Configuração do embedder. Exemplo:
            {
                "provider": "openai",
                "config": {
                    "model": "text-embedding-3-small",
                    "api_key": "your-api-key"
                }
            }
            Ou para Ollama local:
            {
                "provider": "ollama",
                "config": {"model": "mxbai-embed-large"}
            }
    
    Returns:
        Crew configurado e pronto para executar
    
    Examples:
        # Sem memory (default)
        crew = create_crew_with_planning(task)
        
        # Com memory (OpenAI)
        crew = create_crew_with_planning(
            task,
            enable_memory=True,
            embedder_config={
                "provider": "openai",
                "config": {
                    "model": "text-embedding-3-small",
                    "api_key": os.getenv("OPENAI_API_KEY")
                }
            }
        )
        
        # Com memory (Ollama local - sem API externa)
        crew = create_crew_with_planning(
            task,
            enable_memory=True,
            embedder_config={
                "provider": "ollama",
                "config": {"model": "mxbai-embed-large"}
            }
        )
    """
    
    # Criar agentes especializados
    planner = create_technical_planner()
    architect = create_software_architect()
    backend_dev = create_backend_developer()
    database_eng = create_database_engineer()
    devops_eng = create_devops_engineer()
    qa_eng = create_qa_engineer()
    security_eng = create_security_engineer()
    docs_specialist = create_documentation_specialist()
    code_validator = create_code_validator()
    packaging_specialist = create_packaging_specialist()
    
    # Criar manager (opcional - pode usar manager automático)
    # manager = create_project_manager()
    
    # Criar task principal (será decomposta pelo AgentPlanner)
    main_task = Task(
        description=task_description,
        expected_output="""Complete project deliverable including:
        - All source code files
        - Database migrations
        - Docker configuration
        - CI/CD pipeline
        - Comprehensive tests (>=85% coverage)
        - Documentation (README, architecture, API docs)
        - MANIFEST.md
        - Final ZIP package
        
        Everything must be production-ready and fully functional.""",
        agent=planner  # Task inicial atribuída ao planner
    )
    
    # Criar Crew com Planning + Hierarchical
    crew = Crew(
        agents=[
            planner,
            architect,
            backend_dev,
            database_eng,
            devops_eng,
            qa_eng,
            security_eng,
            docs_specialist,
            code_validator,
            packaging_specialist
        ],
        tasks=[main_task],
        process=Process.hierarchical,  # ← Processo hierárquico
        planning=True,  # ← Planning automático
        planning_llm=create_llm(0.8),  # ← LLM Router V3 para planning
        manager_llm=create_llm(0.8),  # ← LLM Router V3 para manager
        # manager_agent=manager,  # ← Opcional: manager customizado
        max_rpm=10,  # ← Rate limiting (10 requests/min)
        verbose=True,
        memory=enable_memory,  # ← Opcional (requer embedder válido)
        cache=enable_memory,  # ← Habilitado junto com memory
        embedder=embedder_config if embedder_config else None  # ← Configurar se fornecido
    )
    
    return crew


# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

def main():
    """Executa crew com task complexa de exemplo."""
    
    print("=" * 80)
    print("🚀 CREWAI COM PLANNING + HIERARCHICAL + LLM ROUTER V3")
    print("=" * 80)
    print()
    
    # Task complexa de exemplo (similar ao relatório)
    task = """
    Build a production-ready multi-tenant TODO platform with the following requirements:
    
    BACKEND (FastAPI + SQLAlchemy):
    - Multi-tenancy with data isolation
    - JWT authentication (access + refresh tokens)
    - RBAC (Role-Based Access Control: admin/user)
    - Rate limiting per user/endpoint
    - Redis caching
    - Celery async tasks (Redis broker)
    - WebSocket notifications
    - Audit logging
    
    OBSERVABILITY (OpenTelemetry):
    - Distributed traces
    - Custom metrics
    - Structured logs
    - OTLP export
    
    INFRASTRUCTURE:
    - Dockerfile for API
    - docker-compose with 7 services (api, db, redis, worker, otel-collector, grafana, prometheus)
    - GitHub Actions CI/CD pipeline
    - Alembic migrations
    - Seed scripts
    - Makefile
    
    QUALITY:
    - pytest test suites (auth, CRUD, RBAC, rate limit, tasks)
    - >=85% coverage
    - Postman collection
    
    DELIVERABLES:
    - Complete source code
    - README.md with setup instructions
    - Architecture documentation
    - MANIFEST.md
    - Final ZIP package
    
    Ensure COMPLETENESS (all imports exist, no missing files).
    """
    
    print("📋 Task Description:")
    print(task)
    print()
    
    # Criar crew (sem memory por padrão)
    print("🔧 Creating Crew with Planning + Hierarchical...")
    crew = create_crew_with_planning(task, enable_memory=False)
    print("✅ Crew created!")
    print("⚠️  Memory: DISABLED (enable with enable_memory=True + embedder_config)")
    print()
    
    # Executar
    print("🚀 Starting execution...")
    print("=" * 80)
    print()
    
    try:
        result = crew.kickoff()
        
        print()
        print("=" * 80)
        print("✅ EXECUTION COMPLETED!")
        print("=" * 80)
        print()
        print("📊 Result:")
        print(result)
        print()
        
    except Exception as e:
        print()
        print("=" * 80)
        print("❌ EXECUTION FAILED!")
        print("=" * 80)
        print()
        print(f"Error: {e}")
        print()
    
    # Estatísticas do LLM Router V3
    print("=" * 80)
    print("📊 LLM ROUTER V3 STATISTICS")
    print("=" * 80)
    print()
    
    router = get_llm_router()
    router.print_stats()
    
    print()
    print("=" * 80)
    print("🏁 DONE!")
    print("=" * 80)


if __name__ == "__main__":
    main()
