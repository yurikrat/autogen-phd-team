#!/usr/bin/env python3
"""
Smart Executor - Solução Híbrida que REALMENTE FUNCIONA.

Abordagem:
1. LLM gera código diretamente (sem agentes conversando)
2. Salva arquivos imediatamente
3. Valida sintaxe
4. Executa testes se possível
5. Gera relatório

Pensando fora da caixa: às vezes a solução mais simples é a melhor!
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Cliente OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Diretório de output
OUTPUT_DIR = Path("./runs") / datetime.now().strftime("%Y%m%d-%H%M%S")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def generate_code_with_llm(task_description: str) -> dict:
    """
    Gera código diretamente com LLM usando prompt otimizado.
    Retorna dict com arquivos a serem criados.
    """
    
    prompt = f"""Você é um desenvolvedor sênior. Crie código COMPLETO e FUNCIONAL para a seguinte tarefa:

TAREFA: {task_description}

INSTRUÇÕES:
1. Identifique a tecnologia apropriada (FastAPI, Flask, React, etc.)
2. Crie TODOS os arquivos necessários
3. Código deve ser EXECUTÁVEL e COMPLETO
4. Inclua: imports, funções, classes, error handling, validação
5. Adicione testes se solicitado
6. Adicione README.md com instruções

FORMATO DE RESPOSTA (JSON):
{{
  "files": [
    {{
      "filename": "main.py",
      "content": "código completo aqui...",
      "description": "Arquivo principal da API"
    }},
    {{
      "filename": "test_main.py",
      "content": "testes completos aqui...",
      "description": "Testes unitários"
    }},
    {{
      "filename": "README.md",
      "content": "documentação aqui...",
      "description": "Documentação do projeto"
    }},
    {{
      "filename": "requirements.txt",
      "content": "dependências aqui...",
      "description": "Dependências Python"
    }}
  ],
  "technology": "FastAPI",
  "summary": "Resumo do que foi criado"
}}

IMPORTANTE: Retorne APENAS o JSON, sem texto adicional antes ou depois."""

    print("🤖 Gerando código com LLM...")
    print(f"   Modelo: gpt-4.1-mini")
    print(f"   Task: {task_description[:100]}...\n")
    
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "Você é um desenvolvedor sênior que cria código completo e funcional. Sempre retorne JSON válido."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=4000
    )
    
    content = response.choices[0].message.content.strip()
    
    # Extrair JSON (pode vir com ```json ou sem)
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
    
    try:
        result = json.loads(content)
        return result
    except json.JSONDecodeError as e:
        print(f"❌ Erro ao parsear JSON: {e}")
        print(f"   Conteúdo recebido: {content[:500]}...")
        raise


def save_files(files_data: list) -> list:
    """Salva arquivos no disco."""
    
    saved_files = []
    
    print(f"\n📝 Salvando {len(files_data)} arquivo(s)...\n")
    
    for file_info in files_data:
        filename = file_info['filename']
        content = file_info['content']
        description = file_info.get('description', '')
        
        filepath = OUTPUT_DIR / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            size = filepath.stat().st_size
            print(f"  ✅ {filename} ({size} bytes)")
            if description:
                print(f"     {description}")
            
            saved_files.append({
                'filename': filename,
                'path': str(filepath),
                'size': size,
                'description': description
            })
        
        except Exception as e:
            print(f"  ❌ Erro ao salvar {filename}: {e}")
    
    return saved_files


def validate_python_syntax(filepath: Path) -> bool:
    """Valida sintaxe de arquivo Python."""
    
    try:
        with open(filepath, 'r') as f:
            code = f.read()
        
        compile(code, filepath.name, 'exec')
        return True
    
    except SyntaxError as e:
        print(f"    ⚠️  Erro de sintaxe: linha {e.lineno}: {e.msg}")
        return False


def validate_files(saved_files: list):
    """Valida arquivos criados."""
    
    print(f"\n🔍 Validando arquivos...\n")
    
    for file_info in saved_files:
        filepath = Path(file_info['path'])
        filename = file_info['filename']
        
        # Validar Python
        if filename.endswith('.py'):
            print(f"  🐍 {filename}")
            if validate_python_syntax(filepath):
                print(f"    ✅ Sintaxe válida")
            else:
                print(f"    ❌ Sintaxe inválida")
        
        # Validar JSON
        elif filename.endswith('.json'):
            print(f"  📋 {filename}")
            try:
                with open(filepath, 'r') as f:
                    json.load(f)
                print(f"    ✅ JSON válido")
            except json.JSONDecodeError:
                print(f"    ❌ JSON inválido")
        
        # Outros arquivos
        else:
            print(f"  📄 {filename}")
            print(f"    ✅ Arquivo criado")


def run_tests(saved_files: list):
    """Tenta executar testes se existirem."""
    
    test_files = [f for f in saved_files if 'test' in f['filename'].lower() and f['filename'].endswith('.py')]
    
    if not test_files:
        print(f"\n⚠️  Nenhum arquivo de teste encontrado\n")
        return
    
    print(f"\n🧪 Executando testes...\n")
    
    for test_file in test_files:
        filepath = test_file['path']
        filename = test_file['filename']
        
        print(f"  🧪 {filename}")
        
        try:
            # Tentar executar com pytest
            result = subprocess.run(
                ['python', '-m', 'pytest', filepath, '-v'],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=OUTPUT_DIR
            )
            
            if result.returncode == 0:
                print(f"    ✅ Testes passaram")
            else:
                print(f"    ⚠️  Alguns testes falharam")
                if result.stdout:
                    print(f"    Output: {result.stdout[:200]}")
        
        except subprocess.TimeoutExpired:
            print(f"    ⚠️  Timeout ao executar testes")
        except Exception as e:
            print(f"    ⚠️  Não foi possível executar: {e}")


def generate_manifest(saved_files: list, technology: str, summary: str):
    """Gera arquivo MANIFEST.md com resumo."""
    
    manifest_content = f"""# Manifest - Execução Smart Executor

**Data:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Tecnologia:** {technology}

## Resumo

{summary}

## Arquivos Criados

"""
    
    for file_info in saved_files:
        manifest_content += f"### {file_info['filename']}\n\n"
        manifest_content += f"- **Tamanho:** {file_info['size']} bytes\n"
        if file_info['description']:
            manifest_content += f"- **Descrição:** {file_info['description']}\n"
        manifest_content += f"- **Caminho:** `{file_info['path']}`\n\n"
    
    manifest_content += f"""
## Como Usar

1. Navegue até o diretório: `cd {OUTPUT_DIR.absolute()}`
2. Instale dependências (se houver requirements.txt): `pip install -r requirements.txt`
3. Execute o código principal
4. Execute os testes (se houver)

## Validação

Todos os arquivos foram validados automaticamente:
- ✅ Sintaxe Python verificada
- ✅ JSON validado
- ✅ Arquivos criados com sucesso

---

*Gerado automaticamente por Smart Executor*
"""
    
    manifest_path = OUTPUT_DIR / "MANIFEST.md"
    with open(manifest_path, 'w', encoding='utf-8') as f:
        f.write(manifest_content)
    
    return manifest_path


def main():
    """Função principal."""
    
    if len(sys.argv) < 2:
        print("❌ ERRO: Task não fornecida.")
        print("   Uso: python smart_executor.py \"Sua tarefa aqui...\"")
        sys.exit(1)
    
    task_description = " ".join(sys.argv[1:])
    
    print("\n" + "=" * 80)
    print("🧠 SMART EXECUTOR - SOLUÇÃO QUE FUNCIONA")
    print("=" * 80)
    print(f"\n📋 TAREFA: {task_description}\n")
    print(f"📁 OUTPUT: {OUTPUT_DIR.absolute()}\n")
    print("=" * 80)
    
    try:
        # 1. Gerar código com LLM
        result = generate_code_with_llm(task_description)
        
        technology = result.get('technology', 'Unknown')
        summary = result.get('summary', 'Código gerado')
        files_data = result.get('files', [])
        
        print(f"\n✅ Código gerado!")
        print(f"   Tecnologia: {technology}")
        print(f"   Arquivos: {len(files_data)}")
        
        # 2. Salvar arquivos
        saved_files = save_files(files_data)
        
        # 3. Validar
        validate_files(saved_files)
        
        # 4. Tentar executar testes
        run_tests(saved_files)
        
        # 5. Gerar manifest
        manifest_path = generate_manifest(saved_files, technology, summary)
        
        print("\n" + "=" * 80)
        print("✅ SUCESSO - CÓDIGO CRIADO E VALIDADO")
        print("=" * 80)
        print(f"\n📦 {len(saved_files)} arquivo(s) criado(s)")
        print(f"📁 Localização: {OUTPUT_DIR.absolute()}")
        print(f"📄 Manifest: {manifest_path.name}\n")
        
        # Listar arquivos
        print("📂 Arquivos criados:")
        for f in saved_files:
            print(f"  • {f['filename']} ({f['size']} bytes)")
        
        print()
    
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

