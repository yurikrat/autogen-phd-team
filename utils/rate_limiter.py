#!/usr/bin/env python3
"""
Rate Limiter - Controla rate limiting e retry para API OpenAI.

Funcionalidades:
- Rate limiting inteligente (delay entre chamadas)
- Retry com backoff exponencial
- Timeout configurável
- Monitoramento de uso
"""

import time
import functools
from typing import Callable, Any
from datetime import datetime, timedelta
import threading


class RateLimiter:
    """Controla rate limiting para evitar timeout da API."""
    
    def __init__(
        self,
        calls_per_minute: int = 20,  # Limite conservador
        min_delay_seconds: float = 1.0  # Delay mínimo entre chamadas
    ):
        self.calls_per_minute = calls_per_minute
        self.min_delay_seconds = min_delay_seconds
        self.call_times = []
        self.lock = threading.Lock()
        
        print(f"🚦 Rate Limiter configurado:")
        print(f"   • Máximo: {calls_per_minute} chamadas/minuto")
        print(f"   • Delay mínimo: {min_delay_seconds}s entre chamadas")
    
    def wait_if_needed(self):
        """Aguarda se necessário para respeitar rate limit."""
        with self.lock:
            now = datetime.now()
            
            # Remover chamadas antigas (mais de 1 minuto)
            self.call_times = [
                t for t in self.call_times 
                if now - t < timedelta(minutes=1)
            ]
            
            # Verificar se atingiu limite
            if len(self.call_times) >= self.calls_per_minute:
                # Calcular quanto tempo esperar
                oldest_call = self.call_times[0]
                wait_until = oldest_call + timedelta(minutes=1)
                wait_seconds = (wait_until - now).total_seconds()
                
                if wait_seconds > 0:
                    print(f"   ⏳ Rate limit atingido - aguardando {wait_seconds:.1f}s...")
                    time.sleep(wait_seconds)
                    now = datetime.now()
            
            # Verificar delay mínimo desde última chamada
            if self.call_times:
                last_call = self.call_times[-1]
                time_since_last = (now - last_call).total_seconds()
                
                if time_since_last < self.min_delay_seconds:
                    wait_seconds = self.min_delay_seconds - time_since_last
                    time.sleep(wait_seconds)
                    now = datetime.now()
            
            # Registrar esta chamada
            self.call_times.append(now)
    
    def get_stats(self) -> dict:
        """Retorna estatísticas de uso."""
        with self.lock:
            now = datetime.now()
            recent_calls = [
                t for t in self.call_times 
                if now - t < timedelta(minutes=1)
            ]
            
            return {
                'calls_last_minute': len(recent_calls),
                'calls_per_minute_limit': self.calls_per_minute,
                'utilization_percent': (len(recent_calls) / self.calls_per_minute) * 100
            }


# Instância global
_global_rate_limiter = None


def get_rate_limiter(
    calls_per_minute: int = 20,
    min_delay_seconds: float = 1.0
) -> RateLimiter:
    """Retorna instância global do rate limiter."""
    global _global_rate_limiter
    
    if _global_rate_limiter is None:
        _global_rate_limiter = RateLimiter(calls_per_minute, min_delay_seconds)
    
    return _global_rate_limiter


def with_rate_limit(func: Callable) -> Callable:
    """Decorator para aplicar rate limiting em funções."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        limiter = get_rate_limiter()
        limiter.wait_if_needed()
        return func(*args, **kwargs)
    
    return wrapper


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator para retry com backoff exponencial.
    
    Args:
        max_retries: Número máximo de tentativas
        initial_delay: Delay inicial em segundos
        backoff_factor: Fator de multiplicação do delay
        exceptions: Tupla de exceções para capturar
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        print(f"   ⚠️  Tentativa {attempt + 1}/{max_retries + 1} falhou: {str(e)[:100]}")
                        print(f"   ⏳ Aguardando {delay:.1f}s antes de tentar novamente...")
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        print(f"   ❌ Todas as {max_retries + 1} tentativas falharam")
                        raise last_exception
            
            raise last_exception
        
        return wrapper
    
    return decorator


class APICallMonitor:
    """Monitora chamadas à API para debugging."""
    
    def __init__(self):
        self.calls = []
        self.lock = threading.Lock()
    
    def record_call(
        self,
        function_name: str,
        duration_seconds: float,
        success: bool,
        error: str = None
    ):
        """Registra uma chamada à API."""
        with self.lock:
            self.calls.append({
                'timestamp': datetime.now().isoformat(),
                'function': function_name,
                'duration': duration_seconds,
                'success': success,
                'error': error
            })
    
    def get_summary(self) -> dict:
        """Retorna resumo das chamadas."""
        with self.lock:
            if not self.calls:
                return {
                    'total_calls': 0,
                    'successful': 0,
                    'failed': 0,
                    'avg_duration': 0,
                    'total_duration': 0
                }
            
            successful = [c for c in self.calls if c['success']]
            failed = [c for c in self.calls if not c['success']]
            durations = [c['duration'] for c in self.calls]
            
            return {
                'total_calls': len(self.calls),
                'successful': len(successful),
                'failed': len(failed),
                'success_rate': (len(successful) / len(self.calls)) * 100,
                'avg_duration': sum(durations) / len(durations),
                'total_duration': sum(durations),
                'recent_errors': [c['error'] for c in failed[-5:] if c['error']]
            }
    
    def print_summary(self):
        """Imprime resumo formatado."""
        summary = self.get_summary()
        
        print("\n📊 RESUMO DE CHAMADAS À API")
        print("=" * 80)
        print(f"Total de chamadas: {summary['total_calls']}")
        print(f"Sucessos: {summary['successful']} ({summary.get('success_rate', 0):.1f}%)")
        print(f"Falhas: {summary['failed']}")
        print(f"Duração média: {summary['avg_duration']:.2f}s")
        print(f"Duração total: {summary['total_duration']:.2f}s")
        
        if summary.get('recent_errors'):
            print("\n❌ Erros recentes:")
            for error in summary['recent_errors']:
                print(f"   • {error[:100]}")
        
        print("=" * 80)


# Instância global do monitor
_global_monitor = APICallMonitor()


def get_api_monitor() -> APICallMonitor:
    """Retorna instância global do monitor."""
    return _global_monitor


def monitored_api_call(func: Callable) -> Callable:
    """Decorator para monitorar chamadas à API."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        monitor = get_api_monitor()
        start_time = time.time()
        success = False
        error = None
        
        try:
            result = func(*args, **kwargs)
            success = True
            return result
        except Exception as e:
            error = str(e)
            raise
        finally:
            duration = time.time() - start_time
            monitor.record_call(func.__name__, duration, success, error)
    
    return wrapper


if __name__ == "__main__":
    # Teste do rate limiter
    print("🧪 Testando Rate Limiter...\n")
    
    limiter = get_rate_limiter(calls_per_minute=10, min_delay_seconds=0.5)
    
    for i in range(5):
        print(f"Chamada {i + 1}...")
        limiter.wait_if_needed()
        time.sleep(0.1)  # Simular processamento
    
    stats = limiter.get_stats()
    print(f"\n📊 Estatísticas:")
    print(f"   Chamadas no último minuto: {stats['calls_last_minute']}")
    print(f"   Utilização: {stats['utilization_percent']:.1f}%")
    
    # Teste do monitor
    monitor = get_api_monitor()
    monitor.record_call("test_function", 1.5, True)
    monitor.record_call("test_function", 2.0, False, "Timeout")
    monitor.print_summary()

