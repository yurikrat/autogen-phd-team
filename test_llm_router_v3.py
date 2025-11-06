#!/usr/bin/env python3
"""
Teste abrangente do LLM Router V3.

Testa:
- Circuit Breaker
- Adaptive Timeout
- Health Check
- Retry com Jitter
- Fallback automático
- Detecção de complexidade
"""

import time
from utils.llm_router import get_llm_router

print("🧪 TESTE COMPLETO DO LLM ROUTER V3\n")
print("=" * 80)

# Inicializar router
router = get_llm_router(
    base_timeout=60,
    max_retries=3,
    auto_complexity_detection=True,
    enable_circuit_breaker=True
)

print("\n✅ Router inicializado com:")
print("   • Circuit Breaker: ATIVADO")
print("   • Adaptive Timeout: ATIVADO")
print("   • Health Check: ATIVADO")
print("   • Retry com Jitter: ATIVADO (3 tentativas)")

# ============================================================================
# TESTE 1: Task Simples (Timeout 60s)
# ============================================================================
print("\n" + "=" * 80)
print("📝 TESTE 1: Task Simples (deve usar deepseek-chat, timeout 60s)")
print("=" * 80)

try:
    start = time.time()
    response = router.call("Diga 'olá' em uma palavra")
    elapsed = time.time() - start
    print(f"✅ Sucesso em {elapsed:.1f}s")
    print(f"Resposta: {response[:100]}")
except Exception as e:
    print(f"❌ Erro: {e}")

time.sleep(2)

# ============================================================================
# TESTE 2: Task Média (Timeout 90s)
# ============================================================================
print("\n" + "=" * 80)
print("📝 TESTE 2: Task Média (deve usar deepseek-chat/reasoner, timeout 90s)")
print("=" * 80)

try:
    start = time.time()
    response = router.call(
        "Crie uma API REST simples com FastAPI contendo endpoints de CRUD para usuários. "
        "Inclua autenticação JWT e validação com Pydantic."
    )
    elapsed = time.time() - start
    print(f"✅ Sucesso em {elapsed:.1f}s")
    print(f"Resposta: {response[:200]}...")
except Exception as e:
    print(f"❌ Erro: {e}")

time.sleep(2)

# ============================================================================
# TESTE 3: Task Complexa (Timeout 120s)
# ============================================================================
print("\n" + "=" * 80)
print("📝 TESTE 3: Task Complexa (deve usar deepseek-reasoner, timeout 120s)")
print("=" * 80)

try:
    start = time.time()
    response = router.call(
        "Construa um sistema completo de e-commerce com backend FastAPI, "
        "frontend React, integração com gateway de pagamento, "
        "sistema de notificações, Docker, CI/CD, testes completos, "
        "documentação e deploy. Liste os principais componentes."
    )
    elapsed = time.time() - start
    print(f"✅ Sucesso em {elapsed:.1f}s")
    print(f"Resposta: {response[:200]}...")
except Exception as e:
    print(f"❌ Erro: {e}")

time.sleep(2)

# ============================================================================
# TESTE 4: Múltiplas Chamadas Rápidas (Stress Test)
# ============================================================================
print("\n" + "=" * 80)
print("📝 TESTE 4: Múltiplas Chamadas Rápidas (stress test)")
print("=" * 80)

success_count = 0
fail_count = 0

for i in range(5):
    try:
        start = time.time()
        response = router.call(f"Responda apenas: teste {i+1}")
        elapsed = time.time() - start
        success_count += 1
        print(f"✅ Chamada {i+1}/5: Sucesso em {elapsed:.1f}s")
    except Exception as e:
        fail_count += 1
        print(f"❌ Chamada {i+1}/5: Erro - {str(e)[:100]}")
    
    time.sleep(1)

print(f"\n📊 Resultado: {success_count}/5 sucessos, {fail_count}/5 falhas")

# ============================================================================
# TESTE 5: Verificar Circuit Breaker States
# ============================================================================
print("\n" + "=" * 80)
print("📝 TESTE 5: Verificar Estados dos Circuit Breakers")
print("=" * 80)

stats = router.get_stats()
print(f"🔵 DeepSeek Circuit Breaker: {stats['deepseek']['circuit_state'].upper()}")
print(f"🟢 OpenAI Circuit Breaker: {stats['openai']['circuit_state'].upper()}")

# ============================================================================
# ESTATÍSTICAS FINAIS
# ============================================================================
print("\n" + "=" * 80)
print("📊 ESTATÍSTICAS FINAIS")
print("=" * 80)

router.print_stats()

print("\n" + "=" * 80)
print("✅ TESTE COMPLETO FINALIZADO!")
print("=" * 80)
