#!/usr/bin/env python3
"""
LLM Router - Roteamento inteligente entre OpenAI e DeepSeek com fallback automático.

Funcionalidades:
- Roteamento automático entre DeepSeek (principal) e OpenAI (fallback)
- Tratamento de timeout e rate limit
- Recuperação automática após cooldown
- Monitoramento de uso e estatísticas
- Compatível com CrewAI BaseLLM
"""

import os
import time
import threading
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from openai import OpenAI
from crewai import BaseLLM


class LLMRouter(BaseLLM):
    """
    Roteador inteligente de LLMs com fallback automático.
    
    Estratégia:
    1. DeepSeek como principal (mais barato)
    2. OpenAI como fallback (mais confiável)
    3. Fallback automático em caso de erro 429, 503, timeout
    4. Recuperação automática após cooldown
    """
    
    def __init__(
        self,
        model: str = "deepseek-chat",
        temperature: Optional[float] = 0.7,
        cooldown_seconds: int = 60,
        max_retries: int = 2,
        timeout: int = 30
    ):
        """
        Inicializa o roteador de LLMs.
        
        Args:
            model: Nome do modelo (usado para DeepSeek)
            temperature: Temperatura para geração
            cooldown_seconds: Tempo de espera após falha antes de tentar DeepSeek novamente
            max_retries: Número máximo de tentativas por API
            timeout: Timeout em segundos para requisições
        """
        # OBRIGATÓRIO: Chamar super().__init__() com model e temperature
        super().__init__(model=model, temperature=temperature)
        
        # Configurações
        self.cooldown_seconds = cooldown_seconds
        self.max_retries = max_retries
        self.timeout = timeout
        
        # Clientes
        self.deepseek_client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com",
            timeout=timeout
        )
        
        self.openai_client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            timeout=timeout
        )
        
        # Estado do roteador
        self.lock = threading.Lock()
        self.deepseek_failures = 0
        self.last_failure_time = None
        self.stats = {
            'deepseek_calls': 0,
            'deepseek_successes': 0,
            'deepseek_failures': 0,
            'openai_calls': 0,
            'openai_successes': 0,
            'openai_failures': 0,
            'total_fallbacks': 0,
            'errors': []
        }
        
        print("🔀 LLM Router inicializado:")
        print(f"   • Principal: DeepSeek ({model})")
        print(f"   • Fallback: OpenAI (gpt-4.1-mini)")
        print(f"   • Cooldown: {cooldown_seconds}s")
        print(f"   • Timeout: {timeout}s")
    
    def call(
        self,
        messages: Union[str, List[Dict[str, str]]],
        tools: Optional[List[dict]] = None,
        callbacks: Optional[List[Any]] = None,
        available_functions: Optional[Dict[str, Any]] = None,
        **kwargs  # Aceitar argumentos adicionais do CrewAI
    ) -> Union[str, Any]:
        """
        Chama o LLM com roteamento inteligente e fallback automático.
        
        Args:
            messages: String ou lista de mensagens
            tools: Lista de tools disponíveis
            callbacks: Callbacks para streaming
            available_functions: Funções disponíveis para function calling
            
        Returns:
            Resposta do LLM como string
        """
        # Converter string para formato de mensagem
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
        
        # Determinar qual API usar
        use_deepseek = self._should_use_deepseek()
        
        if use_deepseek:
            # Tentar DeepSeek primeiro
            try:
                return self._call_deepseek(messages, tools)
            except Exception as e:
                # Registrar falha e tentar OpenAI
                self._record_deepseek_failure(e)
                print(f"   ⚠️  DeepSeek falhou: {str(e)[:100]}")
                print(f"   🔄 Fazendo fallback para OpenAI...")
                
                try:
                    return self._call_openai(messages, tools)
                except Exception as fallback_error:
                    # Ambos falharam
                    error_msg = f"Ambas APIs falharam. DeepSeek: {str(e)[:100]}, OpenAI: {str(fallback_error)[:100]}"
                    self._record_error(error_msg)
                    raise RuntimeError(error_msg)
        else:
            # Usar OpenAI diretamente (DeepSeek em cooldown)
            print(f"   ⏸️  DeepSeek em cooldown, usando OpenAI...")
            try:
                return self._call_openai(messages, tools)
            except Exception as e:
                error_msg = f"OpenAI falhou durante cooldown do DeepSeek: {str(e)[:100]}"
                self._record_error(error_msg)
                raise RuntimeError(error_msg)
    
    def _should_use_deepseek(self) -> bool:
        """Determina se deve usar DeepSeek ou está em cooldown."""
        with self.lock:
            # Se nunca falhou, usar DeepSeek
            if self.deepseek_failures == 0:
                return True
            
            # Se está em cooldown, usar OpenAI
            if self.last_failure_time:
                elapsed = time.time() - self.last_failure_time
                if elapsed < self.cooldown_seconds:
                    return False
            
            # Cooldown expirou, resetar e tentar DeepSeek novamente
            print(f"   ✅ Cooldown expirado, voltando para DeepSeek...")
            self.deepseek_failures = 0
            self.last_failure_time = None
            return True
    
    def _call_deepseek(self, messages: List[Dict], tools: Optional[List] = None) -> str:
        """Chama DeepSeek API com retry."""
        with self.lock:
            self.stats['deepseek_calls'] += 1
        
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                # Preparar payload
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": self.temperature,
                }
                
                # Adicionar tools se fornecido
                if tools and self.supports_function_calling():
                    payload["tools"] = tools
                
                # Fazer chamada
                response = self.deepseek_client.chat.completions.create(**payload)
                
                # Sucesso
                with self.lock:
                    self.stats['deepseek_successes'] += 1
                    self.deepseek_failures = 0
                    self.last_failure_time = None
                
                return response.choices[0].message.content
                
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                
                # Erros que não devem fazer retry (fallback imediato)
                if any(code in error_str for code in ['429', 'rate limit', 'rate_limit']):
                    # Rate limit - fallback imediato (recomendação oficial DeepSeek)
                    raise RuntimeError(f"DeepSeek rate limit reached: {str(e)[:100]}")
                
                elif '503' in error_str or 'overload' in error_str:
                    # Server overloaded - fallback imediato
                    raise RuntimeError(f"DeepSeek server overloaded: {str(e)[:100]}")
                
                elif 'timeout' in error_str:
                    # Timeout - fallback imediato
                    raise RuntimeError(f"DeepSeek timeout: {str(e)[:100]}")
                
                # Outros erros - retry com backoff
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Backoff exponencial
                    print(f"   ⏳ DeepSeek tentativa {attempt + 1}/{self.max_retries} falhou, aguardando {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    # Última tentativa falhou
                    raise RuntimeError(f"DeepSeek failed after {self.max_retries} retries: {str(e)[:100]}")
        
        # Nunca deve chegar aqui, mas por segurança
        raise RuntimeError(f"DeepSeek failed: {str(last_error)[:100]}")
    
    def _call_openai(self, messages: List[Dict], tools: Optional[List] = None) -> str:
        """Chama OpenAI API com retry."""
        with self.lock:
            self.stats['openai_calls'] += 1
            self.stats['total_fallbacks'] += 1
        
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                # Preparar payload
                payload = {
                    "model": "gpt-4.1-mini",  # Modelo OpenAI
                    "messages": messages,
                    "temperature": self.temperature,
                }
                
                # Adicionar tools se fornecido
                if tools and self.supports_function_calling():
                    payload["tools"] = tools
                
                # Fazer chamada
                response = self.openai_client.chat.completions.create(**payload)
                
                # Sucesso
                with self.lock:
                    self.stats['openai_successes'] += 1
                
                return response.choices[0].message.content
                
            except Exception as e:
                last_error = e
                
                # Retry com backoff
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"   ⏳ OpenAI tentativa {attempt + 1}/{self.max_retries} falhou, aguardando {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    # Última tentativa falhou
                    raise RuntimeError(f"OpenAI failed after {self.max_retries} retries: {str(e)[:100]}")
        
        # Nunca deve chegar aqui, mas por segurança
        raise RuntimeError(f"OpenAI failed: {str(last_error)[:100]}")
    
    def _record_deepseek_failure(self, error: Exception):
        """Registra falha do DeepSeek."""
        with self.lock:
            self.deepseek_failures += 1
            self.last_failure_time = time.time()
            self.stats['deepseek_failures'] += 1
    
    def _record_error(self, error_msg: str):
        """Registra erro geral."""
        with self.lock:
            self.stats['errors'].append({
                'timestamp': datetime.now().isoformat(),
                'message': error_msg
            })
            
            # Manter apenas últimos 10 erros
            if len(self.stats['errors']) > 10:
                self.stats['errors'] = self.stats['errors'][-10:]
    
    def supports_function_calling(self) -> bool:
        """Ambos suportam function calling."""
        return True
    
    def supports_stop_words(self) -> bool:
        """Ambos suportam stop words."""
        return True
    
    def get_context_window_size(self) -> int:
        """DeepSeek tem 128K tokens."""
        return 128000
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas de uso."""
        with self.lock:
            total_calls = self.stats['deepseek_calls'] + self.stats['openai_calls']
            
            return {
                'total_calls': total_calls,
                'deepseek': {
                    'calls': self.stats['deepseek_calls'],
                    'successes': self.stats['deepseek_successes'],
                    'failures': self.stats['deepseek_failures'],
                    'success_rate': (self.stats['deepseek_successes'] / self.stats['deepseek_calls'] * 100) 
                                   if self.stats['deepseek_calls'] > 0 else 0
                },
                'openai': {
                    'calls': self.stats['openai_calls'],
                    'successes': self.stats['openai_successes'],
                    'failures': self.stats['openai_failures'],
                    'success_rate': (self.stats['openai_successes'] / self.stats['openai_calls'] * 100)
                                   if self.stats['openai_calls'] > 0 else 0
                },
                'total_fallbacks': self.stats['total_fallbacks'],
                'recent_errors': self.stats['errors'][-5:]
            }
    
    def print_stats(self):
        """Imprime estatísticas formatadas."""
        stats = self.get_stats()
        
        print("\n" + "=" * 80)
        print("📊 ESTATÍSTICAS DO LLM ROUTER")
        print("=" * 80)
        print(f"Total de chamadas: {stats['total_calls']}")
        print(f"Total de fallbacks: {stats['total_fallbacks']}")
        
        print(f"\n🔵 DeepSeek:")
        print(f"   Chamadas: {stats['deepseek']['calls']}")
        print(f"   Sucessos: {stats['deepseek']['successes']}")
        print(f"   Falhas: {stats['deepseek']['failures']}")
        print(f"   Taxa de sucesso: {stats['deepseek']['success_rate']:.1f}%")
        
        print(f"\n🟢 OpenAI:")
        print(f"   Chamadas: {stats['openai']['calls']}")
        print(f"   Sucessos: {stats['openai']['successes']}")
        print(f"   Falhas: {stats['openai']['failures']}")
        print(f"   Taxa de sucesso: {stats['openai']['success_rate']:.1f}%")
        
        if stats['recent_errors']:
            print(f"\n❌ Erros recentes:")
            for error in stats['recent_errors']:
                print(f"   • [{error['timestamp']}] {error['message'][:100]}")
        
        print("=" * 80)


# Instância global
_global_router = None


def get_llm_router(
    model: str = "deepseek-chat",
    temperature: float = 0.7,
    cooldown_seconds: int = 60,
    max_retries: int = 2,
    timeout: int = 30
) -> LLMRouter:
    """Retorna instância global do LLM Router."""
    global _global_router
    
    if _global_router is None:
        _global_router = LLMRouter(
            model=model,
            temperature=temperature,
            cooldown_seconds=cooldown_seconds,
            max_retries=max_retries,
            timeout=timeout
        )
    
    return _global_router


if __name__ == "__main__":
    # Teste do LLM Router
    print("🧪 Testando LLM Router...\n")
    
    router = get_llm_router()
    
    # Teste 1: Chamada simples
    print("Teste 1: Chamada simples")
    try:
        response = router.call("Olá! Responda apenas 'Oi' para confirmar que está funcionando.")
        print(f"✅ Resposta: {response}\n")
    except Exception as e:
        print(f"❌ Erro: {e}\n")
    
    # Teste 2: Múltiplas chamadas
    print("Teste 2: Múltiplas chamadas")
    for i in range(3):
        try:
            response = router.call(f"Diga apenas o número {i+1}")
            print(f"✅ Chamada {i+1}: {response[:50]}")
        except Exception as e:
            print(f"❌ Chamada {i+1} falhou: {e}")
    
    # Estatísticas
    router.print_stats()
