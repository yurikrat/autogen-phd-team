#!/usr/bin/env python3
"""
Teste simplificado do Planning + Hierarchical.

Testa com task média para validar:
- Planning decompõe automaticamente
- Manager delega para agentes
- Circuit Breaker funciona
- Adaptive Timeout funciona
"""

import os
import sys
from pathlib import Path

# Adicionar ao path
sys.path.insert(0, str(Path(__file__).parent))

from crew_with_planning import create_crew_with_planning
from utils.llm_router import get_llm_router

print("=" * 80)
print("🧪 TESTE: PLANNING + HIERARCHICAL + LLM ROUTER V3")
print("=" * 80)
print()

# Task média (não muito complexa para teste rápido)
task = """
Create a simple REST API with FastAPI that includes:

FEATURES:
- User authentication with JWT tokens
- CRUD operations for TODO items
- SQLite database with SQLAlchemy
- Input validation with Pydantic
- Basic error handling

DELIVERABLES:
- main.py (FastAPI app)
- models.py (SQLAlchemy models)
- schemas.py (Pydantic schemas)
- auth.py (JWT authentication)
- requirements.txt
- README.md with setup instructions

Keep it simple but complete. All imports must work.
"""

print("📋 Task Description:")
print(task)
print()

# Criar crew
print("🔧 Creating Crew...")
crew = create_crew_with_planning(task)
print("✅ Crew created with:")
print(f"   • {len(crew.agents)} specialized agents")
print(f"   • Planning: ENABLED")
print(f"   • Process: HIERARCHICAL")
print(f"   • LLM Router V3: ENABLED")
print()

# Executar
print("🚀 Starting execution...")
print("=" * 80)
print()

try:
    result = crew.kickoff()
    
    print()
    print("=" * 80)
    print("✅ EXECUTION COMPLETED!")
    print("=" * 80)
    print()
    print("📊 Result:")
    print(str(result)[:500])
    print()
    
except Exception as e:
    print()
    print("=" * 80)
    print("❌ EXECUTION FAILED!")
    print("=" * 80)
    print()
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    print()

# Estatísticas do LLM Router V3
print("=" * 80)
print("📊 LLM ROUTER V3 STATISTICS")
print("=" * 80)
print()

router = get_llm_router()
router.print_stats()

print()
print("=" * 80)
print("🏁 TEST COMPLETED!")
print("=" * 80)
