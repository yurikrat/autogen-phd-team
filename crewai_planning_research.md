# Pesquisa: Task Decomposition e Planning no CrewAI

## 🎯 Objetivo

Implementar agentes mais granulares e decomposição automática de tasks para evitar travamentos em tarefas complexas.

## 📚 Descobertas do CrewAI

### 1. **Planning Feature** ✅

**O que é:**
- AgentPlanner que planeja tasks step-by-step ANTES de cada iteração
- Adiciona plano detalhado na descrição de cada task
- Usa LLM para criar lógica passo-a-passo

**Como usar:**
```python
my_crew = Crew(
    agents=self.agents,
    tasks=self.tasks,
    process=Process.sequential,
    planning=True,  # ← Ativa planning
    planning_llm="gpt-4o"  # ← LLM para planejar (default: gpt-4o-mini)
)
```

**Benefícios:**
- ✅ Decomposição automática de tasks complexas
- ✅ Plano step-by-step adicionado a cada task
- ✅ Melhora performance e organização
- ✅ Reduz chance de travamentos

### 2. **Hierarchical Process** 🏗️

**O que é:**
- Manager agent que coordena workflow
- Delega tasks baseado em roles e capabilities
- Valida resultados
- Emula estrutura corporativa

**Key Features:**
- **Task Delegation**: Manager aloca tasks entre crew members
- **Result Validation**: Manager avalia outcomes
- **Efficient Workflow**: Estrutura organizada
- **Context Window Respect**: Prioriza contexto importante
- **Max Requests Per Minute**: Controle de rate limiting
- **Max Iterations**: Limite de iterações

**Como usar:**
```python
# Opção 1: Manager automático
project_crew = Crew(
    tasks=[...],
    agents=[researcher, writer],
    manager_llm="gpt-4o",  # ← Manager LLM
    process=Process.hierarchical,  # ← Processo hierárquico
    planning=True,  # ← Combinar com planning!
)

# Opção 2: Manager customizado
manager = Agent(
    role="Project Manager",
    goal="Efficiently manage the crew and ensure high-quality task completion",
    backstory="You're an experienced project manager...",
    allow_delegation=True,  # ← Permite delegação
)

project_crew = Crew(
    tasks=[...],
    agents=[researcher, writer],
    manager_agent=manager,  # ← Manager customizado
    process=Process.hierarchical,
    planning=True,
)
```

**Workflow:**
1. Manager analisa task complexa
2. Delega subtasks para agentes especializados
3. Agentes executam com ferramentas específicas
4. Manager valida resultados
5. Progressão sequencial com oversight

### 3. **Combinação Poderosa** 🚀

**Planning + Hierarchical = Decomposição Automática!**

```python
crew = Crew(
    agents=[planner, architect, developer, tester, validator],
    tasks=[complex_task],
    process=Process.hierarchical,  # Manager coordena
    planning=True,  # AgentPlanner decompõe
    planning_llm="gpt-4o",  # LLM para planning
    manager_llm="gpt-4o",  # LLM para manager
    max_rpm=10,  # Rate limiting
)
```

**Fluxo:**
1. **AgentPlanner** decompõe task complexa em steps
2. **Manager Agent** delega steps para agentes especializados
3. Agentes executam tasks menores em paralelo/sequencial
4. Manager valida cada step
5. Progressão organizada até conclusão

## 💡 Solução Proposta

### Arquitetura Recomendada

**Agentes Especializados (Granulares):**
1. **Planner Agent** - Analisa requisitos e cria plano
2. **Architect Agent** - Define estrutura e arquitetura
3. **Backend Developer Agent** - Implementa backend
4. **Frontend Developer Agent** - Implementa frontend
5. **DevOps Agent** - Docker, CI/CD, infraestrutura
6. **Database Agent** - Migrations, models, schemas
7. **Testing Agent** - Testes unitários e integração
8. **Documentation Agent** - README, docs, comentários
9. **Code Validator Agent** - Valida imports, dependências
10. **Packaging Agent** - MANIFEST, ZIP final

**Processo:**
- **Hierarchical** com manager agent
- **Planning** habilitado
- **LLM Router V3** para todas as chamadas

**Benefícios:**
- ✅ Tasks menores = menos timeout
- ✅ Agentes especializados = melhor qualidade
- ✅ Manager coordena = sem conflitos
- ✅ Planning decompõe = organização
- ✅ Circuit Breaker = resiliência

## 🔍 Exemplo Prático

**Task Complexa Original:**
```
"Construa plataforma TODO multi-tenant com FastAPI, Redis, Celery, 
OTEL, Docker, CI/CD, testes >=85%, Postman, etc"
```

**Com Planning + Hierarchical:**

**AgentPlanner decompõe em:**
1. Analisar requisitos e criar arquitetura
2. Implementar models e database
3. Implementar autenticação JWT + RBAC
4. Implementar CRUD endpoints
5. Implementar Redis caching + rate limiting
6. Implementar Celery tasks
7. Implementar WebSocket notifications
8. Implementar OpenTelemetry
9. Criar Dockerfile e docker-compose
10. Criar CI/CD pipeline
11. Criar testes (auth, CRUD, RBAC, etc)
12. Criar documentação
13. Validar e empacotar

**Manager Agent delega:**
- Steps 1-2 → Architect + Database Agent
- Steps 3-4 → Backend Developer Agent
- Steps 5-6 → Backend Developer + DevOps Agent
- Step 7 → Backend Developer Agent
- Step 8 → DevOps Agent
- Step 9 → DevOps Agent
- Step 10 → DevOps Agent
- Step 11 → Testing Agent
- Step 12 → Documentation Agent
- Step 13 → Code Validator + Packaging Agent

**Resultado:**
- Tasks pequenas (< 5 min cada)
- Execução organizada
- Validação incremental
- Zero travamentos longos

## 📊 Comparação

| Aspecto | Antes (Sequential) | Depois (Hierarchical + Planning) |
|---------|-------------------|----------------------------------|
| **Task size** | 1 task gigante | 10-15 tasks pequenas |
| **Timeout risk** | Alto (18+ min) | Baixo (< 5 min/task) |
| **Coordination** | Manual | Automática (Manager) |
| **Decomposition** | Manual | Automática (Planner) |
| **Validation** | Final | Incremental |
| **Recovery** | Difícil | Fácil (retomar step) |
| **Visibility** | Baixa | Alta (logs por step) |

## 🚀 Implementação

### Passo 1: Criar Agentes Granulares
```python
planner = Agent(
    role="Technical Planner",
    goal="Analyze requirements and create detailed implementation plan",
    backstory="Expert in breaking down complex systems...",
    llm=get_llm_router()  # ← LLM Router V3
)

architect = Agent(
    role="Software Architect",
    goal="Design system architecture and data models",
    backstory="Experienced architect...",
    llm=get_llm_router()
)

# ... mais 8 agentes especializados
```

### Passo 2: Criar Crew com Planning + Hierarchical
```python
crew = Crew(
    agents=[planner, architect, backend_dev, frontend_dev, devops, 
            database, tester, docs, validator, packager],
    tasks=[complex_task],
    process=Process.hierarchical,
    planning=True,
    planning_llm=get_llm_router(),  # ← LLM Router V3
    manager_llm=get_llm_router(),   # ← LLM Router V3
    max_rpm=10,  # Rate limiting
    verbose=True
)
```

### Passo 3: Executar e Monitorar
```python
result = crew.kickoff()

# Circuit Breaker stats
router = get_llm_router()
router.print_stats()
```

## 🎯 Métricas Esperadas

**Com Planning + Hierarchical + LLM Router V3:**
- ✅ Task duration: < 5 min por step
- ✅ Total duration: 30-45 min (vs 60+ min antes)
- ✅ Timeout rate: < 5% (vs 100% antes)
- ✅ Success rate: > 95%
- ✅ Circuit breaker activations: 0-2
- ✅ Fallback rate: < 20%

## 📖 Fontes

1. CrewAI Docs - Hierarchical Process
2. CrewAI Docs - Planning
3. CrewAI Issue #2717 - Decompose complex task into sub-tasks
4. Medium - How To Think In Terms of Tasks & Flows With CrewAI
5. ActiveWizards - Hierarchical AI Agents: A Guide to CrewAI Delegation
