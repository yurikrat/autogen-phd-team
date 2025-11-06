#!/usr/bin/env python3
"""
Teste Simplificado do LLM Router - Valida funcionalidades básicas.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Adicionar path
sys.path.insert(0, str(Path(__file__).parent))

from utils.llm_router import get_llm_router


def main():
    """Executa testes básicos."""
    print("\n" + "=" * 80)
    print("🚀 TESTE SIMPLIFICADO DO LLM ROUTER")
    print("=" * 80)
    
    # Verificar variáveis de ambiente
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("❌ DEEPSEEK_API_KEY não configurada!")
        return False
    
    print("✅ DEEPSEEK_API_KEY configurada")
    
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY não configurada (fallback não funcionará)")
    else:
        print("✅ OPENAI_API_KEY configurada")
    
    # Criar router
    router = get_llm_router()
    
    # Teste 1: Chamada simples
    print("\n" + "=" * 80)
    print("🧪 TESTE 1: Chamada Simples")
    print("=" * 80)
    
    try:
        response = router.call("Responda apenas 'OK'")
        print(f"✅ Resposta: {response[:100]}")
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False
    
    # Teste 2: Múltiplas chamadas
    print("\n" + "=" * 80)
    print("🧪 TESTE 2: Múltiplas Chamadas (10x)")
    print("=" * 80)
    
    successes = 0
    for i in range(10):
        try:
            response = router.call(f"Diga apenas: {i+1}")
            print(f"✅ Chamada {i+1}: OK")
            successes += 1
        except Exception as e:
            print(f"❌ Chamada {i+1}: {str(e)[:50]}")
    
    print(f"\n📊 Resultado: {successes}/10 chamadas bem-sucedidas")
    
    # Teste 3: Formato de mensagens
    print("\n" + "=" * 80)
    print("🧪 TESTE 3: Diferentes Formatos")
    print("=" * 80)
    
    # String
    try:
        r1 = router.call("Teste string")
        print(f"✅ String: OK")
    except Exception as e:
        print(f"❌ String: {e}")
        return False
    
    # Lista de mensagens
    try:
        messages = [
            {"role": "system", "content": "Você é um assistente."},
            {"role": "user", "content": "Teste lista"}
        ]
        r2 = router.call(messages)
        print(f"✅ Lista de mensagens: OK")
    except Exception as e:
        print(f"❌ Lista: {e}")
        return False
    
    # Estatísticas
    print("\n" + "=" * 80)
    print("📊 ESTATÍSTICAS FINAIS")
    print("=" * 80)
    
    router.print_stats()
    
    # Verificar se DeepSeek foi usado
    stats = router.get_stats()
    if stats['deepseek']['calls'] > 0:
        print("\n✅ DeepSeek está sendo usado como API principal")
    else:
        print("\n⚠️  DeepSeek não foi usado (pode estar em cooldown)")
    
    if stats['openai']['calls'] > 0:
        print(f"⚠️  OpenAI foi usado {stats['openai']['calls']} vezes (fallback ativado)")
    else:
        print("✅ Nenhum fallback necessário (DeepSeek 100% estável)")
    
    print("\n" + "=" * 80)
    print("🎯 TESTE CONCLUÍDO COM SUCESSO!")
    print("=" * 80)
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
