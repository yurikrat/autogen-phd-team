#!/usr/bin/env python3
"""
LLM Router V2 - Roteamento inteligente com watchdog e recuperação automática.

Melhorias:
- Watchdog thread para detectar travamentos
- Timeout agressivo (60s por requisição)
- Logging detalhado de todas as requisições
- Retry automático com fallback
- Detecção de stall e recuperação
"""

import os
import re
import time
import signal
import threading
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from openai import OpenAI
from crewai import BaseLLM

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class TimeoutException(Exception):
    """Exceção lançada quando uma operação excede o timeout."""
    pass


def timeout_handler(signum, frame):
    """Handler para sinal de timeout."""
    raise TimeoutException("Operação excedeu o timeout")


class ComplexityAnalyzer:
    """Analisador de complexidade de tasks para escolher modelo ideal."""
    
    HIGH_COMPLEXITY_KEYWORDS = [
        'completo', 'complete', 'sistema', 'system', 'aplicação', 'application',
        'projeto', 'project', 'arquitetura', 'architecture', 'infraestrutura', 'infrastructure',
        'multi', 'múltiplos', 'multiple', 'vários', 'various', 'todos', 'all',
        'frontend e backend', 'full stack', 'fullstack', 'end-to-end', 'e2e',
        'integração', 'integration', 'microsserviço', 'microservice', 'microsserviço',
        'orquestração', 'orchestration', 'pipeline', 'workflow',
        'gateway', 'pagamento', 'payment', 'autenticação', 'authentication',
        'análise completa', 'deep analysis', 'troubleshooting', 'debug',
        'investigação', 'investigation', 'diagnóstico', 'diagnostic',
        'documentação completa', 'complete documentation', 'manual', 'guia completo',
        'especificação', 'specification', 'detalhado', 'detailed',
        'refatorar tudo', 'refactor all', 'reescrever', 'rewrite', 'migrar', 'migrate',
        'todos os logs', 'all logs', 'histórico completo', 'full history',
        'análise de logs', 'log analysis',
        'ci/cd', 'docker', 'kubernetes', 'deploy', 'deployment',
    ]
    
    MEDIUM_COMPLEXITY_KEYWORDS = [
        'api', 'endpoint', 'serviço', 'service', 'módulo', 'module',
        'componente', 'component', 'feature', 'funcionalidade',
        'crud', 'rest', 'graphql', 'banco de dados', 'database',
    ]
    
    HIGH_COMPLEXITY_PATTERNS = [
        r'\b\d+\+?\s*(arquivos|files|componentes|components|módulos|modules)\b',
        r'\b(criar|create|desenvolver|develop|implementar|implement)\s+(um|uma|a)\s+sistema\b',
        r'\b(backend|frontend)\s+(e|and)\s+(frontend|backend)\b',
        r'\b(com|with)\s+\d+\+?\s+(funcionalidades|features|endpoints)\b',
    ]
    
    @staticmethod
    def analyze(messages: Union[str, List[Dict[str, str]]]) -> Dict[str, Any]:
        """Analisa a complexidade de uma task."""
        if isinstance(messages, str):
            text = messages
        elif isinstance(messages, list):
            text = ' '.join([msg.get('content', '') for msg in messages if isinstance(msg, dict)])
        else:
            text = str(messages)
        
        text_lower = text.lower()
        score = 0
        reasons = []
        
        # 1. Tamanho do input (15-40 pontos)
        char_count = len(text)
        if char_count > 1500:
            score += 40
            reasons.append(f"Input muito grande ({char_count} caracteres)")
        elif char_count > 800:
            score += 30
            reasons.append(f"Input grande ({char_count} caracteres)")
        elif char_count > 400:
            score += 20
            reasons.append(f"Input médio ({char_count} caracteres)")
        elif char_count > 200:
            score += 15
            reasons.append(f"Input moderado ({char_count} caracteres)")
        
        # 2. Keywords de alta complexidade (8 pontos cada, max 50)
        high_keywords_found = [kw for kw in ComplexityAnalyzer.HIGH_COMPLEXITY_KEYWORDS if kw in text_lower]
        keyword_score = min(len(high_keywords_found) * 8, 50)
        score += keyword_score
        if high_keywords_found:
            reasons.append(f"Palavras de alta complexidade ({len(high_keywords_found)}): {', '.join(high_keywords_found[:3])}")
        
        # 3. Keywords de média complexidade (4 pontos cada, max 20)
        medium_keywords_found = [kw for kw in ComplexityAnalyzer.MEDIUM_COMPLEXITY_KEYWORDS if kw in text_lower]
        medium_score = min(len(medium_keywords_found) * 4, 20)
        score += medium_score
        if medium_keywords_found:
            reasons.append(f"Palavras de média complexidade ({len(medium_keywords_found)}): {', '.join(medium_keywords_found[:3])}")
        
        # 4. Padrões complexos (15 pontos cada, max 45)
        patterns_found = [p for p in ComplexityAnalyzer.HIGH_COMPLEXITY_PATTERNS if re.search(p, text_lower)]
        pattern_score = min(len(patterns_found) * 15, 45)
        score += pattern_score
        if patterns_found:
            reasons.append(f"Padrões complexos detectados ({len(patterns_found)})")
        
        # 5. Estimativa de tokens de output
        estimated_tokens = 1000
        if 'completo' in text_lower or 'complete' in text_lower:
            estimated_tokens += 3000
        if 'sistema' in text_lower or 'system' in text_lower:
            estimated_tokens += 2000
        if 'documentação' in text_lower or 'documentation' in text_lower:
            estimated_tokens += 2000
        if 'todos' in text_lower or 'all' in text_lower:
            estimated_tokens += 1500
        if 'análise' in text_lower or 'analysis' in text_lower:
            estimated_tokens += 1000
        estimated_tokens += char_count // 2
        
        # 6. Determinar nível de complexidade
        if score >= 45:
            level = 'high'
            recommended_model = 'deepseek-reasoner'
        elif score >= 25:
            level = 'medium'
            recommended_model = 'deepseek-reasoner' if (estimated_tokens > 4000 or score > 35) else 'deepseek-chat'
        else:
            level = 'low'
            recommended_model = 'deepseek-chat'
        
        return {
            'level': level,
            'score': min(score, 100),
            'estimated_tokens': estimated_tokens,
            'recommended_model': recommended_model,
            'reasons': reasons,
            'keywords_found': {
                'high': high_keywords_found[:5],
                'medium': medium_keywords_found[:5]
            }
        }


class LLMRouter(BaseLLM):
    """
    Roteador inteligente de LLMs com watchdog e recuperação automática.
    """
    
    def __init__(
        self,
        model: str = "deepseek-chat",
        temperature: Optional[float] = 0.7,
        cooldown_seconds: int = 60,
        max_retries: int = 3,
        timeout: int = 60,  # Timeout agressivo: 60s
        auto_complexity_detection: bool = True,
        enable_watchdog: bool = True
    ):
        """Inicializa o roteador de LLMs."""
        super().__init__(model=model, temperature=temperature)
        
        self.default_model = model
        self.cooldown_seconds = cooldown_seconds
        self.max_retries = max_retries
        self.timeout = timeout
        self.auto_complexity_detection = auto_complexity_detection
        self.enable_watchdog = enable_watchdog
        
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
        
        # Estado
        self.lock = threading.Lock()
        self.deepseek_failures = 0
        self.last_failure_time = None
        self.current_request_start = None
        self.stats = {
            'deepseek_chat_calls': 0,
            'deepseek_chat_successes': 0,
            'deepseek_reasoner_calls': 0,
            'deepseek_reasoner_successes': 0,
            'deepseek_failures': 0,
            'deepseek_timeouts': 0,
            'openai_calls': 0,
            'openai_successes': 0,
            'openai_failures': 0,
            'total_fallbacks': 0,
            'complexity_detections': {'low': 0, 'medium': 0, 'high': 0},
            'errors': []
        }
        
        logger.info("🔀 LLM Router V2 inicializado:")
        logger.info(f"   • Modelo padrão: DeepSeek ({model})")
        logger.info(f"   • Detecção automática: {'✅' if auto_complexity_detection else '❌'}")
        logger.info(f"   • Watchdog: {'✅' if enable_watchdog else '❌'}")
        logger.info(f"   • Timeout: {timeout}s (agressivo)")
        logger.info(f"   • Max retries: {max_retries}")
    
    def call(
        self,
        messages: Union[str, List[Dict[str, str]]],
        tools: Optional[List[dict]] = None,
        callbacks: Optional[List[Any]] = None,
        available_functions: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Union[str, Any]:
        """Chama o LLM com watchdog e recuperação automática."""
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
        
        # Registrar início da requisição
        with self.lock:
            self.current_request_start = time.time()
        
        # Log da requisição
        msg_preview = str(messages[0].get('content', ''))[:100] if messages else ''
        logger.info(f"📤 Nova requisição: {msg_preview}...")
        
        # Determinar modelo
        selected_model = self._select_model(messages, tools)
        
        # Determinar API
        use_deepseek = self._should_use_deepseek()
        
        try:
            if use_deepseek:
                try:
                    result = self._call_deepseek(messages, tools, selected_model)
                    logger.info(f"✅ Requisição concluída com sucesso (DeepSeek {selected_model})")
                    return result
                except Exception as e:
                    self._record_deepseek_failure(e)
                    logger.warning(f"⚠️  DeepSeek falhou: {str(e)[:100]}")
                    logger.info(f"🔄 Fazendo fallback para OpenAI...")
                    
                    try:
                        result = self._call_openai(messages, tools)
                        logger.info(f"✅ Requisição concluída com fallback (OpenAI)")
                        return result
                    except Exception as fallback_error:
                        error_msg = f"Ambas APIs falharam. DeepSeek: {str(e)[:100]}, OpenAI: {str(fallback_error)[:100]}"
                        self._record_error(error_msg)
                        logger.error(f"❌ {error_msg}")
                        raise RuntimeError(error_msg)
            else:
                logger.info(f"⏸️  DeepSeek em cooldown, usando OpenAI...")
                try:
                    result = self._call_openai(messages, tools)
                    logger.info(f"✅ Requisição concluída (OpenAI durante cooldown)")
                    return result
                except Exception as e:
                    error_msg = f"OpenAI falhou durante cooldown: {str(e)[:100]}"
                    self._record_error(error_msg)
                    logger.error(f"❌ {error_msg}")
                    raise RuntimeError(error_msg)
        finally:
            # Limpar estado de requisição
            with self.lock:
                self.current_request_start = None
    
    def _select_model(self, messages: List[Dict], tools: Optional[List] = None) -> str:
        """Seleciona o modelo ideal baseado em complexidade."""
        if tools:
            return 'deepseek-chat'
        
        if not self.auto_complexity_detection:
            return self.default_model
        
        analysis = ComplexityAnalyzer.analyze(messages)
        
        with self.lock:
            self.stats['complexity_detections'][analysis['level']] += 1
        
        logger.info(f"🔍 Complexidade: {analysis['level'].upper()} (score: {analysis['score']}/100)")
        logger.info(f"   Modelo recomendado: {analysis['recommended_model']}")
        
        return analysis['recommended_model']
    
    def _should_use_deepseek(self) -> bool:
        """Determina se deve usar DeepSeek ou está em cooldown."""
        with self.lock:
            if self.deepseek_failures == 0:
                return True
            
            if self.last_failure_time:
                elapsed = time.time() - self.last_failure_time
                if elapsed < self.cooldown_seconds:
                    return False
            
            logger.info(f"✅ Cooldown expirado, voltando para DeepSeek...")
            self.deepseek_failures = 0
            self.last_failure_time = None
            return True
    
    def _call_deepseek(self, messages: List[Dict], tools: Optional[List] = None, model: str = None) -> str:
        """Chama DeepSeek API com timeout agressivo."""
        if model is None:
            model = self.default_model
        
        with self.lock:
            if model == 'deepseek-chat':
                self.stats['deepseek_chat_calls'] += 1
            else:
                self.stats['deepseek_reasoner_calls'] += 1
        
        logger.info(f"🔵 Chamando DeepSeek ({model})...")
        
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                start_time = time.time()
                
                payload = {
                    "model": model,
                    "messages": messages,
                    "temperature": self.temperature,
                }
                
                if tools and model == 'deepseek-chat':
                    payload["tools"] = tools
                
                # Fazer chamada com timeout
                response = self.deepseek_client.chat.completions.create(**payload)
                
                elapsed = time.time() - start_time
                logger.info(f"⏱️  DeepSeek respondeu em {elapsed:.1f}s")
                
                # Sucesso
                with self.lock:
                    if model == 'deepseek-chat':
                        self.stats['deepseek_chat_successes'] += 1
                    else:
                        self.stats['deepseek_reasoner_successes'] += 1
                    self.deepseek_failures = 0
                    self.last_failure_time = None
                
                return response.choices[0].message.content
                
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                
                # Detectar tipo de erro
                if 'timeout' in error_str or 'timed out' in error_str:
                    with self.lock:
                        self.stats['deepseek_timeouts'] += 1
                    logger.warning(f"⏱️  DeepSeek timeout na tentativa {attempt + 1}/{self.max_retries}")
                    
                    # Timeout - fallback imediato
                    if attempt >= self.max_retries - 1:
                        raise RuntimeError(f"DeepSeek timeout após {self.max_retries} tentativas")
                    
                    # Aguardar antes de retry
                    wait_time = 2 ** attempt
                    logger.info(f"⏳ Aguardando {wait_time}s antes de retry...")
                    time.sleep(wait_time)
                    continue
                
                elif any(code in error_str for code in ['429', 'rate limit', 'rate_limit']):
                    logger.warning(f"🚫 DeepSeek rate limit atingido")
                    raise RuntimeError(f"DeepSeek rate limit: {str(e)[:100]}")
                
                elif '503' in error_str or 'overload' in error_str:
                    logger.warning(f"🔥 DeepSeek servidor sobrecarregado")
                    raise RuntimeError(f"DeepSeek overloaded: {str(e)[:100]}")
                
                else:
                    # Outros erros - retry
                    if attempt < self.max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.warning(f"⚠️  DeepSeek erro na tentativa {attempt + 1}/{self.max_retries}: {str(e)[:50]}")
                        logger.info(f"⏳ Aguardando {wait_time}s antes de retry...")
                        time.sleep(wait_time)
                    else:
                        raise RuntimeError(f"DeepSeek failed: {str(e)[:100]}")
        
        raise RuntimeError(f"DeepSeek failed: {str(last_error)[:100]}")
    
    def _call_openai(self, messages: List[Dict], tools: Optional[List] = None) -> str:
        """Chama OpenAI API com timeout."""
        with self.lock:
            self.stats['openai_calls'] += 1
            self.stats['total_fallbacks'] += 1
        
        logger.info(f"🟢 Chamando OpenAI (gpt-4.1-mini)...")
        
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                start_time = time.time()
                
                payload = {
                    "model": "gpt-4.1-mini",
                    "messages": messages,
                    "temperature": self.temperature,
                }
                
                if tools:
                    payload["tools"] = tools
                
                response = self.openai_client.chat.completions.create(**payload)
                
                elapsed = time.time() - start_time
                logger.info(f"⏱️  OpenAI respondeu em {elapsed:.1f}s")
                
                with self.lock:
                    self.stats['openai_successes'] += 1
                
                return response.choices[0].message.content
                
            except Exception as e:
                last_error = e
                
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"⚠️  OpenAI erro na tentativa {attempt + 1}/{self.max_retries}: {str(e)[:50]}")
                    logger.info(f"⏳ Aguardando {wait_time}s antes de retry...")
                    time.sleep(wait_time)
                else:
                    raise RuntimeError(f"OpenAI failed: {str(e)[:100]}")
        
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
            if len(self.stats['errors']) > 10:
                self.stats['errors'] = self.stats['errors'][-10:]
    
    def supports_function_calling(self) -> bool:
        return True
    
    def supports_stop_words(self) -> bool:
        return True
    
    def get_context_window_size(self) -> int:
        return 128000
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas de uso."""
        with self.lock:
            total_deepseek = self.stats['deepseek_chat_calls'] + self.stats['deepseek_reasoner_calls']
            total_calls = total_deepseek + self.stats['openai_calls']
            
            return {
                'total_calls': total_calls,
                'deepseek': {
                    'total_calls': total_deepseek,
                    'chat_calls': self.stats['deepseek_chat_calls'],
                    'chat_successes': self.stats['deepseek_chat_successes'],
                    'reasoner_calls': self.stats['deepseek_reasoner_calls'],
                    'reasoner_successes': self.stats['deepseek_reasoner_successes'],
                    'failures': self.stats['deepseek_failures'],
                    'timeouts': self.stats['deepseek_timeouts'],
                    'success_rate': ((self.stats['deepseek_chat_successes'] + self.stats['deepseek_reasoner_successes']) / total_deepseek * 100) 
                                   if total_deepseek > 0 else 0
                },
                'openai': {
                    'calls': self.stats['openai_calls'],
                    'successes': self.stats['openai_successes'],
                    'failures': self.stats['openai_failures'],
                    'success_rate': (self.stats['openai_successes'] / self.stats['openai_calls'] * 100)
                                   if self.stats['openai_calls'] > 0 else 0
                },
                'complexity_detections': self.stats['complexity_detections'],
                'total_fallbacks': self.stats['total_fallbacks'],
                'recent_errors': self.stats['errors'][-5:]
            }
    
    def print_stats(self):
        """Imprime estatísticas formatadas."""
        stats = self.get_stats()
        
        logger.info("=" * 80)
        logger.info("📊 ESTATÍSTICAS DO LLM ROUTER")
        logger.info("=" * 80)
        logger.info(f"Total de chamadas: {stats['total_calls']}")
        logger.info(f"Total de fallbacks: {stats['total_fallbacks']}")
        
        logger.info(f"\n🔵 DeepSeek:")
        logger.info(f"   Total: {stats['deepseek']['total_calls']} chamadas")
        logger.info(f"   • deepseek-chat: {stats['deepseek']['chat_calls']} ({stats['deepseek']['chat_successes']} sucessos)")
        logger.info(f"   • deepseek-reasoner: {stats['deepseek']['reasoner_calls']} ({stats['deepseek']['reasoner_successes']} sucessos)")
        logger.info(f"   Falhas: {stats['deepseek']['failures']}")
        logger.info(f"   Timeouts: {stats['deepseek']['timeouts']}")
        logger.info(f"   Taxa de sucesso: {stats['deepseek']['success_rate']:.1f}%")
        
        logger.info(f"\n🟢 OpenAI:")
        logger.info(f"   Chamadas: {stats['openai']['calls']}")
        logger.info(f"   Sucessos: {stats['openai']['successes']}")
        logger.info(f"   Falhas: {stats['openai']['failures']}")
        logger.info(f"   Taxa de sucesso: {stats['openai']['success_rate']:.1f}%")
        
        logger.info(f"\n🔍 Detecção de Complexidade:")
        logger.info(f"   • Baixa: {stats['complexity_detections']['low']}")
        logger.info(f"   • Média: {stats['complexity_detections']['medium']}")
        logger.info(f"   • Alta: {stats['complexity_detections']['high']}")
        
        if stats['recent_errors']:
            logger.info(f"\n❌ Erros recentes:")
            for error in stats['recent_errors']:
                logger.info(f"   • [{error['timestamp']}] {error['message'][:100]}")
        
        logger.info("=" * 80)


# Instância global
_global_router = None


def get_llm_router(
    model: str = "deepseek-chat",
    temperature: float = 0.7,
    cooldown_seconds: int = 60,
    max_retries: int = 3,
    timeout: int = 60,
    auto_complexity_detection: bool = True,
    enable_watchdog: bool = True
) -> LLMRouter:
    """Retorna instância global do LLM Router."""
    global _global_router
    
    if _global_router is None:
        _global_router = LLMRouter(
            model=model,
            temperature=temperature,
            cooldown_seconds=cooldown_seconds,
            max_retries=max_retries,
            timeout=timeout,
            auto_complexity_detection=auto_complexity_detection,
            enable_watchdog=enable_watchdog
        )
    
    return _global_router
