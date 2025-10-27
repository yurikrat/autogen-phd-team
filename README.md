# AutoGen PhD Team Runtime

Sistema de execução de time de agentes AutoGen (v0.4+) com papéis de TI "nível PhD/Nobel", roteamento dinâmico, feedback contínuo e entrega de artefatos.

## 🎯 Objetivo

Criar um runtime Python que permite executar, pelo terminal, um time de agentes AutoGen onde:

- ✅ Você passa uma task como argumento de linha de comando
- ✅ Apenas os agentes necessários são ativados (roteamento dinâmico)
- ✅ Os agentes reportam progresso ao longo do processo
- ✅ Tudo que for produzido é salvo como artefato em `./runs/<timestamp>/`
- ✅ No final, é gerado um `MANIFEST.md` com os caminhos e o time encerra com "CONCLUÍDO"

## 📋 Pré-requisitos

- **Python 3.10+**
- **Conta OpenAI** com API key válida
- **Conexão com internet** (para chamadas à API)
- **Modelos suportados:** gpt-4.1-mini, gpt-4.1-nano, gemini-2.5-flash

## 🚀 Instalação

### 1. Clone o repositório

```bash
git clone <URL_DO_REPOSITORIO>
cd autogen-phd-team
```

### 2. Crie e ative um ambiente virtual

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure a API key

```bash
cp .env.example .env
```

Edite o arquivo `.env` e insira sua chave da OpenAI:

```
OPENAI_API_KEY="sua-chave-aqui"
```

## 💻 Como Usar

### Executar uma task

```bash
python team_runtime.py "Sua tarefa aqui..."
```

### Exemplos

**Exemplo 1: Projeto Backend Completo**
```bash
python team_runtime.py "Criar serviço de reconciliação Pix: API REST (FastAPI), Postgres, ETL diário, dashboard Metabase, CI/CD em Kubernetes; LGPD + OWASP. Entreguem todos os artefatos."
```

**Exemplo 2: Frontend React**
```bash
python team_runtime.py "Criar protótipo de dashboard em React com gráficos interativos, integração com API REST e design responsivo."
```

**Exemplo 3: Pipeline de Dados**
```bash
python team_runtime.py "Implementar pipeline ETL com Airflow para ingerir dados de APIs, transformar com dbt e carregar no BigQuery."
```

**Exemplo 4: Análise de Segurança**
```bash
python team_runtime.py "Realizar análise de segurança OWASP Top 10 em aplicação web, incluindo SAST, DAST e recomendações de remediação."
```

## 📂 Estrutura de Artefatos

Cada execução cria um diretório em `runs/<YYYYMMDD-HHMMSS>/` contendo:

- **progress.log**: Log detalhado de progresso com timestamps
- **artifacts.json**: Registro estruturado de todos os artefatos
- **MANIFEST.md**: Documento consolidado com lista de artefatos e caminhos
- **Artefatos gerados**: Código, documentação, diagramas, configurações, etc.

### Exemplo de estrutura

```
runs/
└── 20250127-143022/
    ├── progress.log
    ├── artifacts.json
    ├── MANIFEST.md
    ├── api_spec.md
    ├── database_schema.sql
    ├── docker-compose.yml
    ├── README_projeto.md
    └── bundle.zip
```

## 🧩 Arquitetura do Sistema

### Núcleo (sempre presente)

- **AI_Orchestrator**: Coordena o time e decompõe a task
- **Project_Manager**: Define marcos e monitora progresso
- **Tech_Architect**: Define arquitetura e padrões técnicos
- **Finalizer**: Consolida artefatos e gera MANIFEST.md

### Papéis Especializados (ativados dinamicamente)

**Engenharia e Desenvolvimento:**
- Backend_Dev, Frontend_Dev, Mobile_Dev, Integration_Engineer

**Dados e Analytics:**
- DBA_Engineer, Data_Engineer, Data_Scientist, BI_Analyst, ML_Engineer

**Infraestrutura e Operações:**
- DevOps_SRE, Cloud_Architect, Network_Admin, SysAdmin

**Segurança e Compliance:**
- SecOps, AppSec, Compliance_Officer, IAM_Engineer

**Qualidade e Release:**
- QA_Engineer, Performance_Engineer, Release_Manager

**Produto e Negócio:**
- UX_UI_Designer, Product_Owner, Business_Analyst

**Suporte e Operações de TI:**
- ITSM_Manager, Support_Engineer, Monitoring_Analyst

**IA e Prompt Engineering:**
- Prompt_Engineer, AI_Security_Officer

### Roteamento Dinâmico

O sistema analisa a task e ativa automaticamente os papéis necessários com base em palavras-chave:

| Palavra-chave | Papel Ativado |
|---------------|---------------|
| "api", "backend", "fastapi" | Backend_Dev |
| "react", "frontend", "ui" | Frontend_Dev |
| "dashboard", "metabase", "kpi" | BI_Analyst |
| "kubernetes", "ci/cd", "terraform" | DevOps_SRE |
| "owasp", "segurança", "appsec" | AppSec |
| ... | ... |

**Fallback:** Se nenhum papel adicional for detectado, `Backend_Dev` é incluído por padrão.

## 🛠️ Tools Disponíveis para os Agentes

Os agentes têm acesso às seguintes tools:

| Tool | Descrição |
|------|-----------|
| `report_progress(stage, message)` | Reporta progresso ao console e progress.log |
| `create_folder(relative_path)` | Cria pasta dentro do run_dir |
| `save_text(name, content, relative_path)` | Salva arquivo .txt |
| `save_markdown(name, markdown, relative_path)` | Salva arquivo .md |
| `save_json(name, data, relative_path)` | Salva arquivo .json |
| `save_file_from_url(url, name, relative_path, timeout)` | Baixa arquivo de URL |
| `save_base64(name, b64_content, relative_path)` | Decodifica base64 e salva |
| `list_artifacts()` | Lista todos os artefatos registrados |
| `zip_run(name)` | Cria ZIP com todos os artefatos |
| `finalize_run()` | Gera MANIFEST.md e finaliza |

## 🔧 Como Estender

### Adicionar Novos Papéis

1. **Edite `roles.py`:**
   - Adicione nova entrada no dicionário `ROLE_MSG`
   - Use o helper `phd_nobel(prefix, domain_expectations)` para manter consistência

2. **Edite `routing.py`:**
   - Adicione o papel ao dicionário `KEYWORDS` com suas palavras-chave
   - Ou adicione ao `CORE_ALWAYS` se deve estar sempre presente

### Adicionar Novas Tools

1. **Edite `tools/io_tools.py`:**
   - Implemente a nova função com type hints
   - Use `get_store()` para acessar o ArtifactStore
   - Retorne dict com `status` e informações relevantes

2. **Edite `team_runtime.py`:**
   - Adicione `FunctionTool(sua_funcao, description="...")` à lista `tools`

### Trocar Estratégia de Roteamento

Para usar **embeddings semânticos** em vez de palavras-chave:

1. Instale biblioteca de embeddings (ex: `sentence-transformers`)
2. Modifique `routing.py` para calcular similaridade entre task e descrições de papéis
3. Selecione top-K papéis mais relevantes

Para usar **RoundRobinGroupChat** (previsível e determinístico):

1. Em `team_runtime.py`, substitua `SelectorGroupChat` por `RoundRobinGroupChat`
2. Defina ordem fixa de participação dos agentes

## 🐛 Troubleshooting

### Problema: "OPENAI_API_KEY não encontrada"

**Solução:**
- Verifique se o arquivo `.env` existe e contém `OPENAI_API_KEY="..."`
- Certifique-se de que o arquivo `.env` está no mesmo diretório que `team_runtime.py`

### Problema: Execução termina antes de gerar artefatos

**Possíveis causas:**
- **MaxMessageTermination atingido**: Aumente o limite em `team_runtime.py` (padrão: 80)
- **Erro na API**: Verifique logs para erros de rate limit ou quota excedida
- **Agentes não estão usando tools**: Revise as mensagens de sistema em `roles.py`

### Problema: Rate limit da OpenAI

**Solução:**
- Aguarde alguns minutos antes de tentar novamente
- Considere usar modelo mais barato (`gpt-4o-mini` em vez de `gpt-4`)
- Reduza `MaxMessageTermination` para limitar número de mensagens

### Problema: Artefatos não aparecem no MANIFEST.md

**Causa:** Agentes não estão chamando as tools `save_*`

**Solução:**
- Reforce nas instruções da task: "Salve TODOS os artefatos usando as tools SAVE_*"
- Verifique se as tools estão sendo passadas corretamente aos agentes em `team_runtime.py`

### Problema: Execução não termina com "CONCLUÍDO"

**Causa:** Finalizer não está sendo ativado ou não está seguindo as instruções

**Solução:**
- Verifique se "Finalizer" está em `CORE_ALWAYS` (deve estar sempre presente)
- Aumente `MaxMessageTermination` para dar mais tempo ao Finalizer
- Revise a mensagem de sistema do Finalizer em `roles.py`

## 📊 Testes Recomendados

### Teste 1: Smoke Test
```bash
python team_runtime.py "Validar URL https://api.github.com e salvar resposta como JSON"
```
**Esperado:** Artefatos criados + MANIFEST.md gerado

### Teste 2: Roteamento Backend
```bash
python team_runtime.py "Criar API REST com FastAPI para CRUD de usuários"
```
**Esperado:** Backend_Dev presente nos logs

### Teste 3: Roteamento BI
```bash
python team_runtime.py "Criar dashboard com KPIs de vendas no Metabase"
```
**Esperado:** BI_Analyst presente nos logs

### Teste 4: Roteamento DevOps
```bash
python team_runtime.py "Configurar pipeline CI/CD com GitHub Actions e deploy no Kubernetes"
```
**Esperado:** DevOps_SRE presente nos logs

### Teste 5: Múltiplos Papéis
```bash
python team_runtime.py "Criar aplicação full-stack: React frontend, FastAPI backend, Postgres, CI/CD, OWASP"
```
**Esperado:** Frontend_Dev, Backend_Dev, DBA_Engineer, DevOps_SRE, AppSec presentes

## 🔒 Segurança e Boas Práticas

- ✅ **Nunca commite o arquivo `.env`** (já está no `.gitignore`)
- ✅ **Use timeouts em requests** (já implementado em `save_file_from_url`)
- ✅ **Limite `MaxMessageTermination`** para controlar custos
- ✅ **Revise artefatos gerados** antes de usar em produção
- ✅ **Rotacione API keys periodicamente**
- ✅ **Monitore uso e custos** no dashboard da OpenAI

## 📝 Licença

MIT License - Sinta-se livre para usar, modificar e distribuir.

## 🤝 Contribuindo

Contribuições são bem-vindas! Para adicionar novos papéis, tools ou melhorias:

1. Fork o repositório
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📧 Suporte

Para dúvidas, problemas ou sugestões, abra uma issue no repositório.

---

**Desenvolvido com ❤️ usando AutoGen v0.4+**

