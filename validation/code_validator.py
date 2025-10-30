#!/usr/bin/env python3
"""
Code Validator - Valida e corrige código automaticamente.

Funcionalidades:
- Validação de sintaxe Python
- Execução de testes pytest
- Linting com pylint/flake8
- Correção automática de erros
- Feedback loop até código passar
"""

import ast
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import json


class CodeValidator:
    """Valida código gerado e força correções."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.validation_results = {
            'syntax': {'passed': False, 'errors': []},
            'tests': {'passed': False, 'errors': []},
            'linting': {'passed': False, 'errors': []},
            'execution': {'passed': False, 'errors': []}
        }
    
    def validate_all(self) -> Tuple[bool, Dict]:
        """
        Valida todos os aspectos do código.
        
        Returns:
            (success, results_dict)
        """
        print("\n🔍 VALIDAÇÃO AUTOMÁTICA DE CÓDIGO")
        print("=" * 80)
        
        # 1. Validar sintaxe
        syntax_ok = self.validate_syntax()
        
        # 2. Validar linting (se sintaxe OK)
        linting_ok = self.validate_linting() if syntax_ok else False
        
        # 3. Executar testes (se sintaxe OK)
        tests_ok = self.run_tests() if syntax_ok else False
        
        # 4. Tentar executar código principal
        execution_ok = self.try_execution() if syntax_ok else False
        
        # Resultado geral
        all_passed = syntax_ok and tests_ok
        
        print("\n" + "=" * 80)
        print(f"📊 RESULTADO GERAL: {'✅ PASSOU' if all_passed else '❌ FALHOU'}")
        print("=" * 80)
        
        return all_passed, self.validation_results
    
    def validate_syntax(self) -> bool:
        """Valida sintaxe de todos os arquivos Python."""
        print("\n1️⃣ Validando sintaxe Python...")
        
        python_files = list(self.output_dir.rglob("*.py"))
        
        if not python_files:
            print("   ⚠️  Nenhum arquivo Python encontrado")
            return False
        
        errors = []
        for filepath in python_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    code = f.read()
                ast.parse(code)
                print(f"   ✅ {filepath.name} - Sintaxe válida")
            except SyntaxError as e:
                error_msg = f"{filepath.name}: Linha {e.lineno} - {e.msg}"
                errors.append(error_msg)
                print(f"   ❌ {error_msg}")
                self.validation_results['syntax']['errors'].append(error_msg)
        
        passed = len(errors) == 0
        self.validation_results['syntax']['passed'] = passed
        
        if passed:
            print(f"   ✅ Todos os {len(python_files)} arquivos têm sintaxe válida")
        
        return passed
    
    def validate_linting(self) -> bool:
        """Valida código com pylint/flake8."""
        print("\n2️⃣ Validando qualidade do código (linting)...")
        
        python_files = list(self.output_dir.rglob("*.py"))
        
        # Tentar flake8 primeiro (mais leve)
        try:
            for filepath in python_files:
                result = subprocess.run(
                    ['python', '-m', 'flake8', '--max-line-length=100', 
                     '--ignore=E501,W503', str(filepath)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    print(f"   ✅ {filepath.name} - Qualidade OK")
                else:
                    print(f"   ⚠️  {filepath.name} - Avisos de qualidade:")
                    print(f"       {result.stdout[:200]}")
                    self.validation_results['linting']['errors'].append(
                        f"{filepath.name}: {result.stdout[:200]}"
                    )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("   ⚠️  Linting não disponível (flake8 não instalado)")
            return True  # Não bloquear se linter não disponível
        
        # Considerar sucesso se não houver erros críticos
        self.validation_results['linting']['passed'] = True
        return True
    
    def run_tests(self) -> bool:
        """Executa testes pytest."""
        print("\n3️⃣ Executando testes...")
        
        test_files = list(self.output_dir.rglob("test_*.py"))
        
        if not test_files:
            print("   ⚠️  Nenhum arquivo de teste encontrado")
            self.validation_results['tests']['passed'] = False
            return False
        
        try:
            # Executar pytest
            result = subprocess.run(
                ['python', '-m', 'pytest', str(self.output_dir), '-v', '--tb=short'],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.output_dir
            )
            
            print(f"   📋 Output dos testes:")
            print("   " + "\n   ".join(result.stdout.split('\n')[:20]))
            
            if result.returncode == 0:
                print(f"   ✅ Todos os testes passaram!")
                self.validation_results['tests']['passed'] = True
                return True
            else:
                print(f"   ❌ Alguns testes falharam")
                self.validation_results['tests']['errors'].append(result.stdout)
                self.validation_results['tests']['passed'] = False
                return False
                
        except subprocess.TimeoutExpired:
            print("   ❌ Testes excederam tempo limite (60s)")
            self.validation_results['tests']['errors'].append("Timeout")
            return False
        except Exception as e:
            print(f"   ❌ Erro ao executar testes: {e}")
            self.validation_results['tests']['errors'].append(str(e))
            return False
    
    def try_execution(self) -> bool:
        """Tenta executar o código principal."""
        print("\n4️⃣ Testando execução do código...")
        
        # Procurar main.py ou app.py
        main_files = list(self.output_dir.glob("main.py")) + \
                    list(self.output_dir.glob("app.py"))
        
        if not main_files:
            print("   ⚠️  Nenhum arquivo main.py/app.py encontrado")
            return True  # Não é erro crítico
        
        main_file = main_files[0]
        
        try:
            # Tentar importar (validação básica)
            result = subprocess.run(
                [sys.executable, '-c', f'import sys; sys.path.insert(0, "{self.output_dir}"); '
                 f'import {main_file.stem}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print(f"   ✅ {main_file.name} pode ser importado")
                self.validation_results['execution']['passed'] = True
                return True
            else:
                print(f"   ❌ Erro ao importar {main_file.name}:")
                print(f"       {result.stderr[:200]}")
                self.validation_results['execution']['errors'].append(result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            print("   ⚠️  Execução excedeu tempo limite")
            return False
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            return False
    
    def generate_feedback_for_correction(self) -> str:
        """
        Gera feedback detalhado para agentes corrigirem código.
        
        Returns:
            String com feedback formatado
        """
        feedback = []
        
        feedback.append("🔍 VALIDAÇÃO AUTOMÁTICA - FEEDBACK PARA CORREÇÃO\n")
        feedback.append("=" * 80 + "\n")
        
        # Erros de sintaxe
        if not self.validation_results['syntax']['passed']:
            feedback.append("❌ ERROS DE SINTAXE:")
            for error in self.validation_results['syntax']['errors']:
                feedback.append(f"   • {error}")
            feedback.append("\n✅ AÇÃO NECESSÁRIA: Corrigir erros de sintaxe Python\n")
        
        # Erros de testes
        if not self.validation_results['tests']['passed']:
            feedback.append("❌ TESTES FALHARAM:")
            for error in self.validation_results['tests']['errors'][:3]:  # Primeiros 3
                feedback.append(f"   • {error[:200]}")
            feedback.append("\n✅ AÇÃO NECESSÁRIA: Corrigir código para testes passarem\n")
        
        # Erros de execução
        if not self.validation_results['execution']['passed']:
            feedback.append("❌ ERROS DE EXECUÇÃO:")
            for error in self.validation_results['execution']['errors'][:2]:
                feedback.append(f"   • {error[:200]}")
            feedback.append("\n✅ AÇÃO NECESSÁRIA: Corrigir imports e dependências\n")
        
        # Avisos de linting
        if self.validation_results['linting']['errors']:
            feedback.append("⚠️  AVISOS DE QUALIDADE:")
            for error in self.validation_results['linting']['errors'][:3]:
                feedback.append(f"   • {error[:150]}")
            feedback.append("\n💡 SUGESTÃO: Melhorar qualidade do código\n")
        
        feedback.append("=" * 80)
        
        return "\n".join(feedback)
    
    def save_validation_report(self):
        """Salva relatório de validação em JSON."""
        report_path = self.output_dir / 'VALIDATION_REPORT.json'
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.validation_results, f, indent=2)
        
        print(f"\n📄 Relatório salvo: {report_path}")


def validate_code_directory(output_dir: Path) -> Tuple[bool, str]:
    """
    Valida código em um diretório.
    
    Args:
        output_dir: Diretório com código gerado
        
    Returns:
        (success, feedback_message)
    """
    validator = CodeValidator(output_dir)
    success, results = validator.validate_all()
    
    # Gerar feedback
    feedback = validator.generate_feedback_for_correction()
    
    # Salvar relatório
    validator.save_validation_report()
    
    return success, feedback


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python code_validator.py <diretório>")
        sys.exit(1)
    
    directory = Path(sys.argv[1])
    
    if not directory.exists():
        print(f"❌ Diretório não encontrado: {directory}")
        sys.exit(1)
    
    success, feedback = validate_code_directory(directory)
    
    print("\n" + feedback)
    
    sys.exit(0 if success else 1)

