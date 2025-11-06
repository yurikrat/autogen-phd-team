#!/usr/bin/env python3
"""
Teste de Detecção de Complexidade - Valida escolha automática de modelo.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Adicionar path
sys.path.insert(0, str(Path(__file__).parent))

from utils.llm_router import get_llm_router, ComplexityAnalyzer


def test_complexity_analyzer():
    """Testa o analisador de complexidade."""
    print("\n" + "=" * 80)
    print("🧪 TESTE: Analisador de Complexidade")
    print("=" * 80)
    
    test_cases = [
        {
            'name': 'Task Simples',
            'prompt': 'Crie uma função Python que soma dois números',
            'expected_level': 'low',
            'expected_model': 'deepseek-chat'
        },
        {
            'name': 'API REST Básica',
            'prompt': 'Crie uma API REST com endpoint de usuários usando FastAPI',
            'expected_level': 'medium',
            'expected_model': 'deepseek-chat'
        },
        {
            'name': 'Microserviço com Integração',
            'prompt': '''
            Crie um microserviço completo de pagamentos com:
            - API REST com FastAPI
            - Integração com Stripe
            - Banco de dados PostgreSQL
            - Testes unitários
            - Docker
            ''',
            'expected_level': 'high',
            'expected_model': 'deepseek-reasoner'
        },
        {
            'name': 'Sistema Multi-camadas Completo',
            'prompt': '''
            Desenvolva um sistema completo de e-commerce com:
            - Backend em Python com FastAPI
            - Frontend em React com TypeScript
            - Banco de dados PostgreSQL com múltiplas tabelas
            - Sistema de autenticação JWT
            - Integração com gateway de pagamento
            - Carrinho de compras com Redis
            - Painel administrativo completo
            - Sistema de notificações por email
            - Upload de imagens com S3
            - Documentação completa da API
            - Testes unitários e de integração
            - Docker e docker-compose
            - CI/CD com GitHub Actions
            - Monitoramento com Prometheus
            ''',
            'expected_level': 'high',
            'expected_model': 'deepseek-reasoner'
        },
        {
            'name': 'Troubleshooting Complexo',
            'prompt': '''
            Analise todos os logs do sistema dos últimos 7 dias e identifique:
            - Erros recorrentes
            - Padrões de falha
            - Gargalos de performance
            - Problemas de memória
            - Sugestões de otimização
            Forneça um relatório detalhado com análise completa.
            ''',
            'expected_level': 'high',
            'expected_model': 'deepseek-reasoner'
        },
        {
            'name': 'Documentação Extensa',
            'prompt': '''
            Crie documentação completa para uma API com 50+ endpoints incluindo:
            - Descrição de cada endpoint
            - Parâmetros e respostas
            - Exemplos de uso
            - Códigos de erro
            - Guia de autenticação
            - Tutoriais passo a passo
            ''',
            'expected_level': 'high',
            'expected_model': 'deepseek-reasoner'
        }
    ]
    
    results = []
    
    for test in test_cases:
        print(f"\n{'─' * 80}")
        print(f"📝 {test['name']}")
        print(f"{'─' * 80}")
        
        analysis = ComplexityAnalyzer.analyze(test['prompt'])
        
        print(f"Prompt: {test['prompt'][:100]}...")
        print(f"\n🔍 Análise:")
        print(f"   • Nível: {analysis['level'].upper()}")
        print(f"   • Score: {analysis['score']}/100")
        print(f"   • Tokens estimados: {analysis['estimated_tokens']}")
        print(f"   • Modelo recomendado: {analysis['recommended_model']}")
        
        if analysis['reasons']:
            print(f"   • Razões:")
            for reason in analysis['reasons']:
                print(f"      - {reason}")
        
        if analysis['keywords_found']['high']:
            print(f"   • Keywords (alta): {', '.join(analysis['keywords_found']['high'])}")
        
        # Verificar se está correto
        level_match = analysis['level'] == test['expected_level']
        model_match = analysis['recommended_model'] == test['expected_model']
        
        if level_match and model_match:
            print(f"\n✅ PASSOU - Detecção correta!")
            results.append(True)
        else:
            print(f"\n⚠️  ATENÇÃO:")
            if not level_match:
                print(f"   Nível esperado: {test['expected_level']}, obtido: {analysis['level']}")
            if not model_match:
                print(f"   Modelo esperado: {test['expected_model']}, obtido: {analysis['recommended_model']}")
            results.append(False)
    
    # Resumo
    print(f"\n{'=' * 80}")
    print(f"📊 RESUMO")
    print(f"{'=' * 80}")
    passed = sum(results)
    total = len(results)
    print(f"Testes passados: {passed}/{total} ({passed/total*100:.1f}%)")
    
    return passed == total


def test_with_real_calls():
    """Testa com chamadas reais para a API."""
    print("\n" + "=" * 80)
    print("🧪 TESTE: Chamadas Reais com Detecção de Complexidade")
    print("=" * 80)
    
    router = get_llm_router(auto_complexity_detection=True)
    
    test_cases = [
        {
            'name': 'Task Simples',
            'prompt': 'Crie uma função Python que calcula fatorial',
            'expected_model': 'deepseek-chat'
        },
        {
            'name': 'Task Média',
            'prompt': 'Crie uma API REST básica com CRUD de produtos usando FastAPI',
            'expected_model': 'deepseek-chat'
        },
        {
            'name': 'Task Complexa',
            'prompt': '''
            Crie um sistema completo de gerenciamento de tarefas com:
            - Backend em Python
            - Frontend em React
            - Autenticação
            - Banco de dados
            - Testes
            ''',
            'expected_model': 'deepseek-reasoner'
        }
    ]
    
    results = []
    
    for test in test_cases:
        print(f"\n{'─' * 80}")
        print(f"📝 {test['name']}")
        print(f"{'─' * 80}")
        
        try:
            response = router.call(test['prompt'])
            print(f"✅ Resposta recebida ({len(response)} caracteres)")
            print(f"Preview: {response[:150]}...")
            results.append(True)
        except Exception as e:
            print(f"❌ Erro: {e}")
            results.append(False)
    
    # Estatísticas
    print(f"\n{'=' * 80}")
    print(f"📊 ESTATÍSTICAS")
    print(f"{'=' * 80}")
    router.print_stats()
    
    # Resumo
    passed = sum(results)
    total = len(results)
    print(f"\n✅ Testes passados: {passed}/{total} ({passed/total*100:.1f}%)")
    
    return passed == total


def main():
    """Executa todos os testes."""
    print("\n" + "=" * 80)
    print("🚀 TESTE DE DETECÇÃO DE COMPLEXIDADE")
    print("=" * 80)
    
    # Verificar variáveis de ambiente
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("❌ DEEPSEEK_API_KEY não configurada!")
        return False
    
    print("✅ DEEPSEEK_API_KEY configurada")
    
    # Teste 1: Analisador de complexidade
    test1_passed = test_complexity_analyzer()
    
    # Teste 2: Chamadas reais
    print("\n\n")
    test2_passed = test_with_real_calls()
    
    # Resultado final
    print("\n" + "=" * 80)
    print("🎯 RESULTADO FINAL")
    print("=" * 80)
    
    if test1_passed and test2_passed:
        print("✅ TODOS OS TESTES PASSARAM!")
        return True
    else:
        print("❌ ALGUNS TESTES FALHARAM")
        if not test1_passed:
            print("   • Analisador de complexidade falhou")
        if not test2_passed:
            print("   • Chamadas reais falharam")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
