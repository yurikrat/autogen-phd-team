#!/usr/bin/env python3
"""
Crew Evolved - Versão evoluída com validação, desafios dinâmicos e memória.

Evoluções:
1. Validação automática de código (executa, testa, corrige)
2. Desafios dinâmicos contextuais (não genéricos)
3. Memória de execuções (aprende com histórico)
4. Feedback loop até código passar
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Importar crew_advanced
sys.path.insert(0, str(Path(__file__).parent))
from crew_advanced import (
    create_architect_agent, create_backend_dev_agent, create_qa_engineer_agent,
    create_security_expert_agent, create_tech_writer_agent, create_tasks,
    ARTIFACTS_BY_AGENT, OUTPUT_DIR
)

from crewai import Crew, Process

# Importar sistemas de validação
from validation.code_validator import validate_code_directory
from validation.dynamic_challenger import challenge_code_directory
from memory.execution_memory import ExecutionMemory

load_dotenv()


def run_evolved_crew(task_description: str, max_iterations: int = 2):
    """
    Executa crew com validação, desafios e memória.
    
    Args:
        task_description: Descrição da tarefa
        max_iterations: Máximo de iterações de correção
    """
    
    print("\n" + "=" * 80)
    print("🧬 CREW EVOLVED - VERSÃO COM VALIDAÇÃO E APRENDIZADO")
    print("=" * 80)
    print(f"\n📋 Tarefa: {task_description}")
    print(f"📁 Output: {OUTPUT_DIR.absolute()}\n")
    print("=" * 80 + "\n")
    
    # Inicializar memória
    memory = ExecutionMemory()
    
    # 1. BUSCAR EXECUÇÕES SIMILARES
    print("🔍 Buscando execuções similares no histórico...")
    similar = memory.find_similar_executions(task_description, limit=3)
    
    if similar:
        print(f"\n✅ Encontradas {len(similar)} execuções similares:")
        for i, exec_info in enumerate(similar, 1):
            status = "✅ Sucesso" if exec_info['success'] else "❌ Falhou"
            print(f"   {i}. {status} - {exec_info['timestamp'][:10]} - "
                  f"{exec_info['total_artifacts']} artefatos")
        
        # Mostrar padrões de sucesso
        patterns = memory.get_success_patterns()
        if patterns:
            print("\n💡 Padrões de sucesso identificados:")
            for pattern in patterns:
                print(f"   • {pattern['description']}")
    else:
        print("   ℹ️  Nenhuma execução similar encontrada (primeira vez)")
    
    print("\n" + "=" * 80 + "\n")
    
    start_time = time.time()
    iteration = 1
    validation_passed = False
    
    while iteration <= max_iterations and not validation_passed:
        print(f"\n{'🔄 ITERAÇÃO ' + str(iteration) if iteration > 1 else '🚀 EXECUÇÃO INICIAL'}")
        print("=" * 80 + "\n")
        
        try:
            # 2. CRIAR AGENTES
            print("👥 Criando agentes especializados...\n")
            agents = {
                'architect': create_architect_agent(),
                'backend': create_backend_dev_agent(),
                'qa': create_qa_engineer_agent(),
                'security': create_security_expert_agent(),
                'writer': create_tech_writer_agent()
            }
            
            # 3. CRIAR TASKS
            print("📋 Criando tasks sequenciais...\n")
            tasks = create_tasks(task_description, agents)
            
            # 4. EXECUTAR CREW
            print("🎼 Iniciando execução do crew...\n")
            print("=" * 80 + "\n")
            
            crew = Crew(
                agents=list(agents.values()),
                tasks=tasks,
                process=Process.sequential,
                verbose=True
            )
            
            result = crew.kickoff()
            
            print("\n" + "=" * 80)
            print("✅ EXECUÇÃO DO CREW CONCLUÍDA")
            print("=" * 80 + "\n")
            
            # 5. VALIDAÇÃO AUTOMÁTICA
            print("\n" + "=" * 80)
            print("🔍 FASE DE VALIDAÇÃO")
            print("=" * 80)
            
            validation_passed, feedback = validate_code_directory(OUTPUT_DIR)
            
            if validation_passed:
                print("\n✅ VALIDAÇÃO PASSOU! Código está pronto.")
                break
            else:
                print("\n⚠️  VALIDAÇÃO FALHOU!")
                print(feedback)
                
                if iteration < max_iterations:
                    print(f"\n🔄 Iniciando iteração {iteration + 1} para correções...")
                    iteration += 1
                else:
                    print(f"\n⚠️  Máximo de iterações ({max_iterations}) atingido.")
                    print("   Código gerado mas pode ter problemas.")
        
        except Exception as e:
            print(f"\n❌ ERRO NA EXECUÇÃO: {e}")
            import traceback
            traceback.print_exc()
            break
    
    execution_time = time.time() - start_time
    
    # 6. DESAFIOS DINÂMICOS
    print("\n" + "=" * 80)
    print("🎯 FASE DE DESAFIOS DINÂMICOS")
    print("=" * 80)
    
    challenges = challenge_code_directory(OUTPUT_DIR)
    
    total_challenges = sum(len(c) for c in challenges.values())
    print(f"\n✅ {total_challenges} desafios contextuais gerados!")
    
    # 7. SALVAR NA MEMÓRIA
    print("\n" + "=" * 80)
    print("💾 SALVANDO NA MEMÓRIA")
    print("=" * 80 + "\n")
    
    # Contar artefatos
    total_artifacts = sum(len(artifacts) for artifacts in ARTIFACTS_BY_AGENT.values())
    
    # Coletar erros se houver
    errors = []
    if not validation_passed:
        errors.append("Validação não passou completamente")
    
    # Salvar execução
    execution_id = memory.save_execution(
        task_description=task_description,
        output_dir=OUTPUT_DIR,
        success=validation_passed,
        validation_passed=validation_passed,
        total_artifacts=total_artifacts,
        execution_time=execution_time,
        agents_used=list(ARTIFACTS_BY_AGENT.keys()),
        errors=errors if errors else None,
        metadata={
            'iterations': iteration,
            'challenges_generated': total_challenges
        }
    )
    
    # Salvar artefatos
    all_artifacts = []
    for agent_name, artifacts in ARTIFACTS_BY_AGENT.items():
        all_artifacts.extend(artifacts)
    
    if all_artifacts:
        memory.save_artifacts(execution_id, all_artifacts)
    
    # 8. ESTATÍSTICAS FINAIS
    print("\n" + "=" * 80)
    print("📊 RESUMO FINAL")
    print("=" * 80)
    
    print(f"\n✅ Execução ID: {execution_id}")
    print(f"⏱️  Tempo total: {execution_time:.1f}s")
    print(f"📦 Artefatos criados: {total_artifacts}")
    print(f"🔄 Iterações: {iteration}")
    print(f"✅ Validação: {'PASSOU' if validation_passed else 'FALHOU'}")
    print(f"🎯 Desafios gerados: {total_challenges}")
    print(f"📁 Localização: {OUTPUT_DIR.absolute()}")
    
    # Mostrar estatísticas gerais
    print("\n")
    memory.print_statistics()
    
    # Lições aprendidas
    lessons = memory.learn_from_failures()
    if lessons and len(lessons) > 1:
        print("\n💡 LIÇÕES APRENDIDAS COM FALHAS:")
        for lesson in lessons[:3]:
            print(f"   • {lesson}")
    
    print("\n" + "=" * 80)
    print("🎉 CREW EVOLVED CONCLUÍDO!")
    print("=" * 80 + "\n")


def main():
    if len(sys.argv) < 2:
        print("❌ Uso: python crew_evolved.py \"Sua tarefa...\"")
        sys.exit(1)
    
    task_description = " ".join(sys.argv[1:])
    
    try:
        run_evolved_crew(task_description, max_iterations=2)
    except KeyboardInterrupt:
        print("\n\n⚠️  Execução interrompida pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERRO FATAL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

