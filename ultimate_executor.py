#!/usr/bin/env python3
"""
Ultimate Executor - A solução DEFINITIVA que funciona.

Abordagem:
- Gera arquivos um por um (não JSON complexo)
- LLM focado em criar código, não conversar
- Validação imediata
- Simples e direto

Pensando como especialista: simplicidade > complexidade
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
OUTPUT_DIR = Path("./runs") / datetime.now().strftime("%Y%m%d-%H%M%S")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def generate_file(task_description: str, file_type: str, context: str = "") -> tuple:
    """
    Gera um arquivo específico.
    
    Args:
        task_description: Descrição da tarefa
        file_type: 'main_code', 'tests', 'readme', 'requirements'
        context: Contexto de arquivos anteriores
    
    Returns:
        (filename, content)
    """
    
    prompts = {
        'main_code': f"""Crie o código principal para: {task_description}

Retorne APENAS o código, sem explicações.
Código deve ser COMPLETO e EXECUTÁVEL.
Inclua imports, classes, funções, error handling.

Primeira linha deve ser o nome do arquivo como comentário: # filename: main.py""",
        
        'tests': f"""Crie testes pytest completos para o código abaixo.

CÓDIGO:
{context}

Retorne APENAS o código de testes, sem explicações.
Primeira linha: # filename: test_main.py

Inclua:
- Testes unitários
- Casos de sucesso e erro
- Fixtures se necessário""",
        
        'readme': f"""Crie um README.md completo para o projeto.

TAREFA: {task_description}

CÓDIGO CRIADO:
{context}

Retorne APENAS o conteúdo do README em Markdown.
Primeira linha: # filename: README.md

Inclua:
- Descrição do projeto
- Como instalar
- Como usar (com exemplos)
- Como rodar testes
- Estrutura de arquivos""",
        
        'requirements': f"""Liste as dependências Python necessárias.

CÓDIGO:
{context}

Retorne APENAS as dependências, uma por linha.
Primeira linha: # filename: requirements.txt

Formato: package==version""",
    }
    
    prompt = prompts.get(file_type, "")
    
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "Você é um desenvolvedor sênior. Retorne apenas código/conteúdo, sem explicações."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=2000
    )
    
    content = response.choices[0].message.content.strip()
    
    # Remover marcadores de código (```python, ```, etc.)
    if content.startswith('```'):
        lines_temp = content.split('\n')
        # Remover primeira linha se for marcador
        if lines_temp[0].startswith('```'):
            lines_temp = lines_temp[1:]
        # Remover última linha se for marcador
        if lines_temp and lines_temp[-1].strip() == '```':
            lines_temp = lines_temp[:-1]
        content = '\n'.join(lines_temp)
    
    # Extrair filename da primeira linha
    lines = content.split('\n')
    filename = None
    
    for i, line in enumerate(lines):
        if 'filename:' in line.lower():
            # Extrair nome do arquivo
            filename = line.split('filename:')[1].strip().strip('#').strip()
            # Remover essa linha do conteúdo
            content = '\n'.join(lines[i+1:])
            break
    
    # Fallback para nomes padrão
    if not filename:
        default_names = {
            'main_code': 'main.py',
            'tests': 'test_main.py',
            'readme': 'README.md',
            'requirements': 'requirements.txt'
        }
        filename = default_names.get(file_type, 'output.txt')
    
    return filename, content.strip()


def save_file(filename: str, content: str) -> dict:
    """Salva arquivo e retorna info."""
    
    filepath = OUTPUT_DIR / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    size = filepath.stat().st_size
    
    return {
        'filename': filename,
        'path': str(filepath),
        'size': size
    }


def validate_python(filepath: Path) -> bool:
    """Valida sintaxe Python."""
    try:
        with open(filepath, 'r') as f:
            compile(f.read(), filepath.name, 'exec')
        return True
    except SyntaxError:
        return False


def main():
    if len(sys.argv) < 2:
        print("❌ Uso: python ultimate_executor.py \"Sua tarefa...\"")
        sys.exit(1)
    
    task = " ".join(sys.argv[1:])
    
    print("\n" + "=" * 80)
    print("🚀 ULTIMATE EXECUTOR")
    print("=" * 80)
    print(f"\n📋 Tarefa: {task}")
    print(f"📁 Output: {OUTPUT_DIR.absolute()}\n")
    print("=" * 80 + "\n")
    
    files_created = []
    
    try:
        # 1. Gerar código principal
        print("📝 [1/4] Gerando código principal...")
        filename, content = generate_file(task, 'main_code')
        file_info = save_file(filename, content)
        files_created.append(file_info)
        print(f"    ✅ {filename} ({file_info['size']} bytes)")
        
        # Validar se Python
        if filename.endswith('.py'):
            if validate_python(Path(file_info['path'])):
                print(f"    ✅ Sintaxe válida")
            else:
                print(f"    ⚠️  Sintaxe com problemas")
        
        main_code = content
        
        # 2. Gerar testes
        print("\n🧪 [2/4] Gerando testes...")
        filename, content = generate_file(task, 'tests', main_code)
        file_info = save_file(filename, content)
        files_created.append(file_info)
        print(f"    ✅ {filename} ({file_info['size']} bytes)")
        
        if filename.endswith('.py'):
            if validate_python(Path(file_info['path'])):
                print(f"    ✅ Sintaxe válida")
            else:
                print(f"    ⚠️  Sintaxe com problemas")
        
        # 3. Gerar README
        print("\n📚 [3/4] Gerando documentação...")
        filename, content = generate_file(task, 'readme', main_code)
        file_info = save_file(filename, content)
        files_created.append(file_info)
        print(f"    ✅ {filename} ({file_info['size']} bytes)")
        
        # 4. Gerar requirements
        print("\n📦 [4/4] Gerando requirements...")
        filename, content = generate_file(task, 'requirements', main_code)
        file_info = save_file(filename, content)
        files_created.append(file_info)
        print(f"    ✅ {filename} ({file_info['size']} bytes)")
        
        # Gerar MANIFEST
        print("\n📄 Gerando MANIFEST...")
        manifest = f"""# Manifest

**Data:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Tarefa:** {task}

## Arquivos Criados

"""
        for f in files_created:
            manifest += f"- **{f['filename']}** ({f['size']} bytes)\n"
        
        manifest += f"""
## Como Usar

```bash
cd {OUTPUT_DIR.absolute()}
pip install -r requirements.txt
python {files_created[0]['filename']}
pytest {files_created[1]['filename']}
```

---
*Gerado por Ultimate Executor*
"""
        
        manifest_info = save_file("MANIFEST.md", manifest)
        files_created.append(manifest_info)
        print(f"    ✅ MANIFEST.md ({manifest_info['size']} bytes)")
        
        # Resumo final
        print("\n" + "=" * 80)
        print("✅ SUCESSO - CÓDIGO CRIADO")
        print("=" * 80)
        print(f"\n📦 {len(files_created)} arquivos criados:")
        for f in files_created:
            print(f"  • {f['filename']}")
        
        print(f"\n📁 Localização: {OUTPUT_DIR.absolute()}")
        print(f"\n💡 Para usar:")
        print(f"   cd {OUTPUT_DIR.absolute()}")
        print(f"   pip install -r requirements.txt")
        print(f"   python {files_created[0]['filename']}\n")
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

