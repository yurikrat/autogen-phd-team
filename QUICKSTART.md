# 🚀 Guia de Início Rápido - AutoGen PhD Team

## ⚡ Setup em 3 Minutos

### 1. Clone e Instale

```bash
# Clone o repositório
git clone https://github.com/yurikrat/autogen-phd-team.git
cd autogen-phd-team

# Crie ambiente virtual
python3 -m venv .venv

# Ative o ambiente
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\Activate.ps1  # Windows PowerShell

# Instale dependências
pip install -r requirements.txt
```

### 2. Configure API Key

```bash
# Copie o exemplo
cp .env.example .env

# Edite e adicione sua chave OpenAI
# OPENAI_API_KEY="sk-..."
nano .env  # ou use seu editor favorito
```

### 3. Execute!

**Modo Visual (Recomendado):**
```bash
python team_runtime_visual.py "Criar API REST para gerenciamento de tarefas com FastAPI, incluindo CRUD completo, autenticação JWT e documentação OpenAPI"
```

O dashboard abrirá automaticamente em `http://localhost:5000` 🎨

**Modo Terminal:**
```bash
python team_runtime.py "Sua tarefa aqui..."
```

## 🎯 Exemplos Práticos

### Backend Completo
```bash
python team_runtime_visual.py "Criar serviço de pagamentos: API REST (FastAPI), Postgres, Redis cache, workers Celery, testes pytest, CI/CD GitHub Actions, deploy Docker"
```

### Frontend Moderno
```bash
python team_runtime_visual.py "Criar dashboard React com TypeScript: componentes reutilizáveis, estado com Zustand, integração API, testes Jest, Tailwind CSS, responsivo"
```

### Arquitetura Escalável
```bash
python team_runtime_visual.py "Projetar arquitetura de microserviços para e-commerce: API Gateway, serviços (produtos, pedidos, pagamentos), bancos, cache, filas, observabilidade. Tech_Architect deve desafiar todas as decisões."
```

### Segurança Completa
```bash
python team_runtime_visual.py "Análise de segurança OWASP Top 10: SAST, DAST, threat modeling, controles de segurança, políticas de acesso, plano de resposta a incidentes. SecOps deve atacar mentalmente cada componente."
```

## 📊 O Que Esperar?

### No Dashboard Visual

1. **Agentes Ativos** (esquerda): Lista de papéis participando
2. **Mapa de Interações** (centro-topo): Grafo mostrando colaboração
3. **Stream de Mensagens** (centro-baixo): Conversas em tempo real
4. **Métricas** (direita-topo): Contadores ao vivo
5. **Artefatos** (direita-baixo): Arquivos sendo criados

### Mensagens Especiais

- 🎯 **DESAFIO**: Agente provocando outro para melhorar
- ✅ **MELHORIA**: Otimização implementada
- ⚠️ **RISCO**: Problema identificado
- 📦 **ARTEFATO**: Arquivo criado

### Artefatos Gerados

Tudo é salvo em `runs/<YYYYMMDD-HHMMSS>/`:
- Código fonte
- Documentação
- Diagramas
- Configurações
- Testes
- `MANIFEST.md` (índice completo)
- `progress.log` (histórico detalhado)

## 🎭 Como os Agentes Se Provocam?

### Exemplo Real de Interação:

```
[AI_Orchestrator]
"Vamos criar uma API REST para gerenciamento de usuários."

[Backend_Dev]
"Implementando endpoints CRUD com FastAPI..."

[Tech_Architect] 🎯 DESAFIO
"Você considerou a escalabilidade desta solução para 10x o volume atual?
Como esta arquitetura se comporta em cenários de falha parcial?"

[Backend_Dev] ✅ MELHORIA
"Boa observação! Adicionando:
- Cache Redis para reduzir carga no banco
- Circuit breaker para resiliência
- Rate limiting para proteção
- Health checks para observabilidade"

[SecOps] 🎯 DESAFIO
"Esta implementação está protegida contra os OWASP Top 10?
Como você garante que dados sensíveis não vazem nos logs?"

[Backend_Dev] ✅ MELHORIA
"Implementando:
- Validação de input com Pydantic
- Sanitização de logs (mascaramento de PII)
- Autenticação JWT com refresh tokens
- Rate limiting por IP
- CORS configurado corretamente"

[QA_Engineer] 🎯 DESAFIO
"Como você validaria esta funcionalidade em produção?
Quais cenários de edge case não foram cobertos?"

[Backend_Dev] ✅ MELHORIA
"Adicionando testes:
- Testes unitários (pytest)
- Testes de integração (TestClient)
- Testes de carga (Locust)
- Testes de segurança (OWASP ZAP)"

[Finalizer]
"Consolidando artefatos... CONCLUÍDO ✅"
```

## 🔧 Dicas Pro

### 1. Maximize a Provocação

Adicione na task:
```
"...e TODOS os agentes devem desafiar-se mutuamente para garantir excelência máxima."
```

### 2. Force Revisões

```
"...Tech_Architect deve revisar TODAS as decisões técnicas."
```

### 3. Exija Métricas

```
"...incluir métricas de performance (latência p99 < 100ms)."
```

### 4. Peça Documentação

```
"...documentação completa com diagramas e exemplos."
```

### 5. Especifique Qualidade

```
"...cobertura de testes > 80%, OWASP Top 10 coberto, padrões SOLID."
```

## ⚙️ Configurações Avançadas

### Ajustar Número de Rodadas

Edite `team_runtime_visual.py`:
```python
max_turns=len(agents) * 10,  # Mais rodadas = mais provocação
```

### Mudar Modelo

Edite `team_runtime_visual.py`:
```python
model="gpt-4.1-mini",  # Rápido e barato
model="gpt-4.1-nano",  # Ainda mais barato
model="gemini-2.5-flash",  # Alternativa Google
```

### Adicionar Novo Papel

1. Edite `roles.py` - adicione mensagem de sistema
2. Edite `routing.py` - adicione palavras-chave
3. Edite `orchestration.py` - adicione comportamento de desafio (opcional)

## 🐛 Troubleshooting Rápido

**Dashboard não abre?**
```bash
pip install flask flask-socketio python-socketio
```

**Erro de API key?**
```bash
# Verifique se .env existe e tem a chave
cat .env
```

**Agentes não respondem?**
- Verifique se o modelo está correto (`gpt-4.1-mini`)
- Aumente `max_turns` para dar mais tempo
- Verifique rate limits da OpenAI

**Artefatos não aparecem?**
- Verifique `runs/<timestamp>/`
- Leia `progress.log` para debug
- Confirme que agentes estão chamando as tools

## 📚 Próximos Passos

1. ✅ Execute o exemplo básico
2. ✅ Explore o dashboard visual
3. ✅ Teste com sua própria task
4. ✅ Leia `README_VISUAL.md` para detalhes
5. ✅ Customize papéis e comportamentos
6. ✅ Integre com seu workflow

## 💡 Ideias de Tasks

- **Migração de Sistema**: "Migrar aplicação monolítica para microserviços"
- **Otimização**: "Otimizar performance de API que está com latência alta"
- **Refatoração**: "Refatorar código legado aplicando Clean Architecture"
- **Documentação**: "Criar documentação completa de sistema existente"
- **Testes**: "Adicionar cobertura de testes em projeto sem testes"
- **Segurança**: "Realizar auditoria de segurança e implementar correções"
- **Deploy**: "Configurar CI/CD completo com testes e deploy automatizado"

## 🎓 Recursos

- **README.md**: Documentação completa original
- **README_VISUAL.md**: Guia do dashboard visual
- **roles.py**: Veja todos os papéis disponíveis
- **examples/**: Exemplos de tasks complexas (em breve)

---

**Pronto para começar?** 🚀

```bash
python team_runtime_visual.py "Sua tarefa incrível aqui..."
```

**Divirta-se vendo os agentes se provocarem para criar soluções de excelência!** 🎼

