# Dockerfile para AutoGen PhD Team
FROM python:3.11-slim

# Metadata
LABEL maintainer="AutoGen PhD Team"
LABEL description="Sistema de agentes AutoGen com inteligência contextual"

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primeiro (para cache de layers)
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Criar diretórios necessários
RUN mkdir -p /app/runs /app/logs

# Expor porta da aplicação web
EXPOSE 8000

# Variáveis de ambiente padrão
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000')" || exit 1

# Comando padrão: iniciar aplicação web
CMD ["python", "web/app.py"]

