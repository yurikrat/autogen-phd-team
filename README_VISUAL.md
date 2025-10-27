# 🎼 AutoGen PhD Team Orchestra - Dashboard Visual em Tempo Real

Sistema avançado de execução de time de agentes AutoGen (v0.4+) com:
- ✅ **Papéis de TI "nível PhD/Nobel"**
- ✅ **Sistema de Provocação e Evolução** - Agentes se desafiam mutuamente
- ✅ **Dashboard Web em Tempo Real** - Visualização ao vivo da colaboração
- ✅ **Gráfico de Interações** - Mapa visual de quem está falando com quem
- ✅ **Métricas de Performance** - Acompanhar progresso e qualidade
- ✅ **Roteamento Dinâmico** - Apenas agentes necessários são ativados
- ✅ **Entrega de Artefatos** - Tudo salvo em `./runs/<timestamp>/`

## 🎯 O Que Torna Este Sistema Único?

### 1. **Orquestra Colaborativa com Provocação**

Os agentes não apenas executam tarefas - eles se **desafiam mutuamente** para elevar a qualidade:

- **Tech_Architect** questiona: *"Você considerou a escalabilidade desta solução para 10x o volume atual?"*
- **SecOps** ataca: *"Esta implementação está protegida contra os OWASP Top 10?"*
- **QA_Engineer** desafia: *"Como você validaria esta funcionalidade em produção?"*
- **Performance_Engineer** provoca: *"Qual é a complexidade algorítmica desta solução?"*

Cada agente é programado para **não aceitar soluções medianas** e forçar melhorias contínuas.

### 2. **Visualização em Tempo Real**

Dashboard web moderno que mostra:

- **Mapa de Interações**: Grafo visual de quem está falando com quem
- **Stream de Mensagens**: Conversas e desafios em tempo real
- **Métricas Ao Vivo**: Mensagens, artefatos, desafios, melhorias
- **Status dos Agentes**: Quem está ativo, quantas mensagens enviou
- **Artefatos Gerados**: Lista atualizada de arquivos criados

### 3. **Comportamento "PhD/Nobel"**

Cada agente segue princípios de excelência:

- **Clareza e Precisão**: Comunicação objetiva e estruturada
- **Análise de Riscos**: Identificação proativa de problemas
- **Critérios de Aceite**: Validação mensurável de entregas
- **Feedback Contínuo**: Progresso reportado constantemente
- **Segurança by Default**: Prioridade em todas as decisões
- **Decisões Acionáveis**: Recomendações práticas e implementáveis

## 🚀 Como Usar

### Instalação Rápida

```bash
# 1. Clone o repositório
git clone <URL_DO_REPOSITORIO>
cd autogen-phd-team

# 2. Crie ambiente virtual
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\Activate.ps1  # Windows

# 3. Instale dependências
pip install -r requirements.txt

# 4. Configure API key
cp .env.example .env
# Edite .env e adicione sua OPENAI_API_KEY
```

### Execução com Dashboard Visual

```bash
python team_runtime_visual.py "Sua tarefa aqui..."
```

O dashboard abrirá automaticamente em `http://localhost:5000` e você verá:

- 🎨 **Interface moderna** com tema dark
- 📊 **Métricas em tempo real** atualizando a cada segundo
- 💬 **Stream de conversas** entre os agentes
- 🔗 **Grafo de interações** mostrando colaboração
- 📦 **Lista de artefatos** sendo criados

### Exemplos de Tasks

**1. Projeto Backend Completo com Provocação:**
```bash
python team_runtime_visual.py "Criar serviço de reconciliação Pix: API REST (FastAPI), Postgres, ETL diário, dashboard Metabase, CI/CD em Kubernetes; LGPD + OWASP. Entreguem todos os artefatos e desafiem-se mutuamente para garantir excelência."
```

**2. Arquitetura Escalável:**
```bash
python team_runtime_visual.py "Projetar arquitetura de microserviços para e-commerce com 1M de usuários simultâneos. Incluir: API Gateway, serviços, bancos, cache, filas, observabilidade. Tech_Architect e Performance_Engineer devem desafiar todas as decisões."
```

**3. Análise de Segurança Profunda:**
```bash
python team_runtime_visual.py "Realizar análise de segurança OWASP Top 10 em aplicação web, incluindo SAST, DAST, threat modeling e recomendações de remediação. SecOps deve atacar mentalmente cada componente."
```

## 🎭 Sistema de Provocação e Evolução

### Como Funciona?

1. **Agentes Especializados**: Cada papel tem expertise específica
2. **Desafios Constantes**: Após cada entrega, outros agentes questionam
3. **Melhorias Iterativas**: Soluções são refinadas em múltiplas rodadas
4. **Métricas de Qualidade**: Dashboard rastreia desafios e melhorias

### Exemplos de Provocações Reais:

**Tech_Architect → Backend_Dev:**
> "Você considerou a escalabilidade desta solução para 10x o volume atual? Como esta arquitetura se comporta em cenários de falha parcial?"

**SecOps → Todos:**
> "Esta implementação está protegida contra os OWASP Top 10? Como você garante que dados sensíveis não vazem nos logs?"

**QA_Engineer → Developer:**
> "Como você validaria esta funcionalidade em produção? Quais cenários de edge case não foram cobertos?"

**Performance_Engineer → Backend_Dev:**
> "Qual é a complexidade algorítmica desta solução? Existem gargalos óbvios que podem ser otimizados?"

## 📊 Dashboard - Recursos Visuais

### Tela Principal

```
┌─────────────────────────────────────────────────────────────┐
│  🎼 AutoGen PhD Team Orchestra          [Status: Running]   │
├──────────┬────────────────────────────────┬─────────────────┤
│          │                                │                 │
│  Agentes │   Mapa de Interações (Grafo)  │    Métricas     │
│  Ativos  │                                │                 │
│          │   ○──────○──────○             │  Mensagens: 45  │
│  ● Orch  │   │      │      │             │  Artefatos: 12  │
│  ● Tech  │   ○──────○──────○             │  Desafios: 8    │
│  ● Back  │                                │  Melhorias: 5   │
│  ● SecOps│                                │                 │
│          ├────────────────────────────────┤                 │
│          │                                │  Artefatos      │
│          │   Stream de Mensagens          │  Gerados:       │
│          │                                │                 │
│          │  [Orch] Coordenando task...   │  ✓ api_spec.md  │
│          │  [Tech] 🎯 DESAFIO: Você      │  ✓ schema.sql   │
│          │         considerou...          │  ✓ docker.yml   │
│          │  [Back] Implementando...       │  ✓ README.md    │
│          │  [SecOps] ⚠️ Risco detectado  │                 │
└──────────┴────────────────────────────────┴─────────────────┘
```

### Cores e Indicadores

- 🟢 **Verde**: Agente ativo, mensagem normal
- 🟡 **Amarelo**: Desafio lançado
- 🔵 **Azul**: Melhoria implementada
- 🔴 **Vermelho**: Erro ou risco identificado
- ⚡ **Pulsante**: Agente processando

## 🧩 Arquitetura do Sistema

### Componentes Principais

1. **team_runtime_visual.py**: Runtime principal com dashboard integrado
2. **orchestration.py**: Sistema de provocação e evolução
3. **dashboard/app.py**: Servidor Flask com WebSocket
4. **dashboard/templates/dashboard.html**: Interface web moderna
5. **roles.py**: Mensagens de sistema "PhD/Nobel" aprimoradas
6. **routing.py**: Seleção dinâmica de papéis
7. **tools/**: Ferramentas de I/O e gerenciamento de artefatos

### Fluxo de Execução

```
1. Usuário executa task
2. Dashboard inicia em background
3. Agentes são selecionados dinamicamente
4. Execução começa com RoundRobinGroupChat
5. Cada mensagem é enviada ao dashboard via WebSocket
6. Agentes se provocam e melhoram soluções
7. Artefatos são salvos e exibidos em tempo real
8. Finalizer consolida e gera MANIFEST.md
9. Dashboard continua acessível para revisão
```

## 🔧 Configuração Avançada

### Ajustar Nível de Provocação

Edite `orchestration.py` para controlar intensidade dos desafios:

```python
# Mais agressivo
CHALLENGE_FREQUENCY = "always"  # Desafia em toda mensagem

# Moderado (padrão)
CHALLENGE_FREQUENCY = "often"   # Desafia frequentemente

# Suave
CHALLENGE_FREQUENCY = "sometimes"  # Desafia ocasionalmente
```

### Customizar Dashboard

Edite `dashboard/templates/dashboard.html` para:
- Mudar cores e tema
- Adicionar gráficos personalizados
- Modificar layout
- Adicionar filtros e buscas

### Adicionar Novos Papéis com Provocação

1. Adicione em `roles.py`:
```python
"Meu_Papel": phd_nobel(
    prefix="Você é o **Meu Papel**...",
    domain_expectations="..."
)
```

2. Adicione comportamento de desafio em `orchestration.py`:
```python
ENHANCED_SYSTEM_MESSAGES["Meu_Papel"] = """
...
**Comportamento de Desafio:**
- Questione X
- Exija Y
- Proponha Z
"""
```

3. Adicione palavras-chave em `routing.py`:
```python
KEYWORDS["Meu_Papel"] = ["palavra1", "palavra2", ...]
```

## 📈 Métricas e KPIs

O dashboard rastreia:

- **Total de Mensagens**: Quantidade de interações
- **Total de Artefatos**: Arquivos gerados
- **Desafios Lançados**: Quantas vezes agentes provocaram outros
- **Melhorias Feitas**: Quantas otimizações foram implementadas
- **Agentes Ativos**: Quantos papéis estão participando
- **Tempo de Execução**: Duração total da task

## 🐛 Troubleshooting

### Dashboard não abre

```bash
# Verifique se Flask está instalado
pip install flask flask-socketio python-socketio

# Verifique se porta 5000 está livre
lsof -i :5000  # Linux/Mac
netstat -ano | findstr :5000  # Windows
```

### Agentes não se provocam

- Verifique se `orchestration.py` está sendo importado
- Confirme que `inject_challenge_behavior()` está sendo chamado
- Aumente `max_turns` para dar mais rodadas de interação

### Dashboard não atualiza

- Verifique console do navegador (F12) para erros WebSocket
- Confirme que `emit_event()` está sendo chamado
- Reinicie o servidor do dashboard

## 🎓 Boas Práticas

### Para Tasks Complexas

1. **Seja Específico**: Quanto mais detalhes, melhor a orquestração
2. **Mencione Desafios**: Peça explicitamente que agentes se provoquem
3. **Defina Critérios**: Especifique métricas de qualidade esperadas
4. **Dê Tempo**: Use `max_turns` alto para tasks complexas

### Para Máxima Qualidade

1. **Ative Papéis de Qualidade**: QA, Performance, SecOps
2. **Force Revisões**: Peça que Tech_Architect revise tudo
3. **Exija Testes**: Solicite cobertura de testes
4. **Peça Documentação**: Sempre inclua docs e diagramas

## 📝 Licença

MIT License - Use, modifique e distribua livremente.

## 🤝 Contribuindo

Contribuições são bem-vindas! Áreas de interesse:

- Novos papéis especializados
- Melhorias no dashboard
- Algoritmos de provocação mais sofisticados
- Integração com ferramentas externas
- Testes automatizados

## 📧 Suporte

Para dúvidas, problemas ou sugestões, abra uma issue no repositório.

---

**Desenvolvido com ❤️ e muita provocação construtiva usando AutoGen v0.4+**

🎼 *"A excelência não é um ato, mas um hábito de desafiar constantemente."*

