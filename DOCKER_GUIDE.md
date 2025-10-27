# 🐳 Guia Docker - AutoGen PhD Team

## 📦 Containerização Completa

Este projeto está 100% containerizado e pronto para rodar em qualquer ambiente.

## 🚀 Início Rápido

### Opção 1: Docker Compose (Recomendado)

```bash
# 1. Clone o repositório
git clone https://github.com/yurikrat/autogen-phd-team.git
cd autogen-phd-team

# 2. Configure a API key
echo "OPENAI_API_KEY=sua-chave-aqui" > .env

# 3. Inicie o container
docker-compose up -d

# 4. Acesse a interface web
# Abra http://localhost:8000 no navegador
```

### Opção 2: Docker Build Manual

```bash
# 1. Build da imagem
docker build -t autogen-phd-team .

# 2. Run do container
docker run -d \
  -p 8000:8000 \
  -e OPENAI_API_KEY=sua-chave-aqui \
  -v $(pwd)/runs:/app/runs \
  --name autogen-phd-team \
  autogen-phd-team

# 3. Acesse http://localhost:8000
```

## 🎯 Como Usar a Interface Web

1. **Abra o navegador:** http://localhost:8000

2. **Digite sua tarefa:**
   ```
   Exemplo: Criar API REST para gerenciamento de produtos com:
   - Endpoints CRUD completos
   - Autenticação JWT
   - Validação de dados com Pydantic
   - Testes unitários com pytest
   - Documentação Swagger automática
   ```

3. **Clique em "🚀 Executar Tarefa"**

4. **Acompanhe em tempo real:**
   - **💬 Conversas:** Veja os agentes trabalhando
   - **📦 Artefatos:** Arquivos sendo criados
   - **🔍 Validação:** Score de qualidade ao final

5. **Artefatos salvos em:** `./runs/YYYYMMDD-HHMMSS/`

## 📊 Gerenciamento do Container

### Ver logs em tempo real
```bash
docker-compose logs -f
```

### Parar o container
```bash
docker-compose down
```

### Reiniciar o container
```bash
docker-compose restart
```

### Ver status
```bash
docker-compose ps
```

### Entrar no container (debug)
```bash
docker-compose exec autogen-phd-team bash
```

## 🔧 Configuração Avançada

### Variáveis de Ambiente

Edite o arquivo `.env`:

```bash
# Obrigatório
OPENAI_API_KEY=sk-...

# Opcional
PORT=8000
SECRET_KEY=sua-chave-secreta-aqui
```

### Customizar Porta

```bash
# docker-compose.yml
ports:
  - "3000:8000"  # Acesse em http://localhost:3000
```

### Persistência de Dados

Os volumes já estão configurados:
- `./runs` - Artefatos gerados
- `./logs` - Logs da aplicação

## 🌍 Deploy em Produção

### Deploy em VPS/Cloud

```bash
# 1. SSH no servidor
ssh user@seu-servidor.com

# 2. Clone e configure
git clone https://github.com/yurikrat/autogen-phd-team.git
cd autogen-phd-team
echo "OPENAI_API_KEY=sua-chave" > .env

# 3. Inicie com Docker Compose
docker-compose up -d

# 4. Configure nginx (opcional)
# Proxy reverso para domínio personalizado
```

### Deploy no Heroku

```bash
# 1. Login no Heroku
heroku login

# 2. Criar app
heroku create seu-app-name

# 3. Configurar API key
heroku config:set OPENAI_API_KEY=sua-chave

# 4. Deploy
git push heroku master

# 5. Abrir
heroku open
```

### Deploy no Railway

```bash
# 1. Instalar Railway CLI
npm install -g @railway/cli

# 2. Login
railway login

# 3. Iniciar projeto
railway init

# 4. Configurar variáveis
railway variables set OPENAI_API_KEY=sua-chave

# 5. Deploy
railway up
```

### Deploy no Render

1. Conecte seu repositório GitHub
2. Configure variáveis de ambiente
3. Deploy automático!

## 🔒 Segurança

### Não commitar .env
O arquivo `.env` está no `.gitignore` - **NUNCA** commite sua API key!

### Usar secrets em produção
```bash
# Docker secrets (Swarm)
echo "sua-chave" | docker secret create openai_key -

# Kubernetes secrets
kubectl create secret generic openai-key \
  --from-literal=OPENAI_API_KEY=sua-chave
```

## 🐛 Troubleshooting

### Container não inicia
```bash
# Ver logs
docker-compose logs

# Verificar se porta está em uso
lsof -i :8000

# Rebuild forçado
docker-compose build --no-cache
docker-compose up -d
```

### API key não funciona
```bash
# Verificar se variável foi passada
docker-compose exec autogen-phd-team env | grep OPENAI

# Recriar container com nova key
docker-compose down
echo "OPENAI_API_KEY=nova-chave" > .env
docker-compose up -d
```

### Artefatos não persistem
```bash
# Verificar volumes
docker-compose exec autogen-phd-team ls -la /app/runs

# Verificar permissões
chmod -R 755 ./runs
```

## 📈 Monitoramento

### Health Check
```bash
# Verificar saúde do container
docker inspect --format='{{.State.Health.Status}}' autogen-phd-team
```

### Métricas
```bash
# Uso de recursos
docker stats autogen-phd-team
```

## 🔄 Atualização

```bash
# 1. Pull nova versão
git pull origin master

# 2. Rebuild
docker-compose build

# 3. Restart
docker-compose down
docker-compose up -d
```

## 💡 Dicas

### Desenvolvimento Local
```bash
# Usar código local (hot reload)
docker-compose -f docker-compose.dev.yml up
```

### Múltiplas Instâncias
```bash
# Escalar horizontalmente
docker-compose up -d --scale autogen-phd-team=3
```

### Backup de Runs
```bash
# Backup automático
tar -czf backup-$(date +%Y%m%d).tar.gz runs/
```

## 📚 Recursos

- **Documentação Docker:** https://docs.docker.com
- **Docker Compose:** https://docs.docker.com/compose
- **Best Practices:** https://docs.docker.com/develop/dev-best-practices

---

**🎉 Sistema 100% containerizado e pronto para produção!**

