# FastAPI Items API

## Descrição

Este projeto é uma API REST simples criada com FastAPI para gerenciar uma lista de itens em memória. Cada item possui um `id`, um `name` e uma `description`. A API permite listar todos os itens e criar novos itens, garantindo que IDs duplicados não sejam permitidos.

## Instalação

1. Clone o repositório:

```bash
git clone <url-do-repositorio>
cd <nome-do-diretorio>
```

2. Crie e ative um ambiente virtual (opcional, mas recomendado):

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate   # Windows
```

3. Instale as dependências:

```bash
pip install fastapi uvicorn pytest
```

## Como usar

1. Para iniciar o servidor FastAPI, execute:

```bash
python main.py
```

2. A API estará disponível em `http://0.0.0.0:8000`.

3. Endpoints:

- `GET /items`: Retorna a lista de itens.
- `POST /items`: Cria um novo item. JSON esperado: `{ "id": int, "name": str, "description": str }`.

### Exemplos de código

- Requisição GET para obter itens:

```python
import requests
response = requests.get("http://localhost:8000/items")
print(response.json())
```

- Requisição POST para criar item:

```python
import requests
item = {"id": 1, "name": "Item 1", "description": "Um item de exemplo"}
response = requests.post("http://localhost:8000/items", json=item)
print(response.status_code)
print(response.json())
```

## Como rodar os testes

1. Certifique-se de que `pytest` está instalado (veja seção instalação).
2. Execute:

```bash
pytest
```

Os testes irão validar as funcionalidades da API como criação e listagem de itens, além da validação dos dados.

## Estrutura do projeto

```
.
├── main.py        # Código principal da API FastAPI
├── test_main.py   # Testes automatizados
├── README.md      # Documentação
```

---

Projeto simples para gerenciar itens via API com FastAPI, ideal para aprendizado e expansão para casos reais.