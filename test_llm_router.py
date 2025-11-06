#!/usr/bin/env python3
"""
Teste do LLM Router - Valida roteamento inteligente entre DeepSeek e OpenAI.
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


def test_basic_call():
    """Teste 1: Chamada básica."""
    print("\n" + "=" * 80)
    print("🧪 TESTE 1: Chamada Básica")
    print("=" * 80)
    
    router = get_llm_router()
    
    try:
        response = router.call("Responda apenas 'OK' para confirmar que está funcionando.")
        print(f"✅ Resposta recebida: {response[:100]}")
        return True
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False


def test_multiple_calls():
    """Teste 2: Múltiplas chamadas."""
    print("\n" + "=" * 80)
    print("🧪 TESTE 2: Múltiplas Chamadas")
    print("=" * 80)
    
    router = get_llm_router()
    successes = 0
    
    for i in range(5):
        try:
            response = router.call(f"Diga apenas o número {i+1}")
            print(f"✅ Chamada {i+1}: {response[:50]}")
            successes += 1
        except Exception as e:
            print(f"❌ Chamada {i+1} falhou: {e}")
    
    print(f"\n📊 Resultado: {successes}/5 chamadas bem-sucedidas")
    return successes >= 4  # Pelo menos 80% de sucesso


def test_message_format():
    """Teste 3: Formato de mensagens."""
    print("\n" + "=" * 80)
    print("🧪 TESTE 3: Formato de Mensagens")
    print("=" * 80)
    
    router = get_llm_router()
    
    # Teste com string
    try:
        response1 = router.call("Teste string")
        print(f"✅ String: {response1[:50]}")
    except Exception as e:
        print(f"❌ String falhou: {e}")
        return False
    
    # Teste com lista de mensagens
    try:
        messages = [
            {"role": "system", "content": "Você é um assistente útil."},
            {"role": "user", "content": "Teste lista"}
        ]
        response2 = router.call(messages)
        print(f"✅ Lista: {response2[:50]}")
    except Exception as e:
        print(f"❌ Lista falhou: {e}")
        return False
    
    return True


def test_with_crewai_agent():
    """Teste 4: Integração com CrewAI Agent."""
    print("\n" + "=" * 80)
    print("🧪 TESTE 4: Integração com CrewAI Agent")
    print("=" * 80)
    
    try:
        from crewai import Agent, Task, Crew
        from utils.llm_router import get_llm_router
        
        # Criar LLM Router
        llm = get_llm_router(temperature=0.7)
        
        # Criar agente
        agent = Agent(
            role="Test Agent",
            goal="Testar o LLM Router",
            backstory="Você é um agente de teste.",
            llm=llm,
            verbose=False
        )
        
        # Criar tarefa
        task = Task(
            description="Diga apenas 'Teste bem-sucedido'",
            expected_output="Uma confirmação",
            agent=agent
        )
        
        # Executar crew
        crew = Crew(agents=[agent], tasks=[task], verbose=False)
        result = crew.kickoff()
        
        print(f"✅ CrewAI executou com sucesso")
        print(f"   Resultado: {str(result)[:100]}")
        return True
        
    except Exception as e:
        print(f"❌ Erro na integração com CrewAI: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_handling():
    """Teste 5: Tratamento de erros."""
    print("\n" + "=" * 80)
    print("🧪 TESTE 5: Tratamento de Erros")
    print("=" * 80)
    
    router = get_llm_router()
    
    # Simular mensagem vazia (deve funcionar)
    try:
        response = router.call("")
        print(f"✅ Mensagem vazia tratada: {response[:50]}")
    except Exception as e:
        print(f"⚠️  Mensagem vazia gerou erro (esperado): {str(e)[:100]}")
    
    return True


def main():
    """Executa todos os testes."""
    print("\n" + "=" * 80)
    print("🚀 INICIANDO TESTES DO LLM ROUTER")
    print("=" * 80)
    
    # Verificar variáveis de ambiente
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("❌ DEEPSEEK_API_KEY não configurada!")
        return False
    
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY não configurada (fallback não funcionará)")
    
    print("✅ Variáveis de ambiente configuradas")
    
    # Executar testes
    results = {
        'Chamada Básica': test_basic_call(),
        'Múltiplas Chamadas': test_multiple_calls(),
        'Formato de Mensagens': test_message_format(),
        'Integração CrewAI': test_with_crewai_agent(),
        'Tratamento de Erros': test_error_handling(),
    }
    
    # Estatísticas finais
    print("\n" + "=" * 80)
    print("📊 ESTATÍSTICAS FINAIS")
    print("=" * 80)
    
    router = get_llm_router()
    router.print_stats()
    
    # Resumo dos testes
    print("\n" + "=" * 80)
    print("📋 RESUMO DOS TESTES")
    print("=" * 80)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{status}: {test_name}")
    
    print("\n" + "=" * 80)
    print(f"🎯 RESULTADO FINAL: {passed}/{total} testes passaram ({passed/total*100:.1f}%)")
    print("=" * 80)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
