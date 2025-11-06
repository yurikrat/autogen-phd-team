#!/usr/bin/env python3
"""
LLM Router V3 - Roteamento inteligente com circuit breaker e adaptive timeout.

Melhorias V3:
- Circuit Breaker para prevenir travamentos
- Adaptive Timeout baseado em complexidade
- Health Check proativo das APIs
- Retry com Exponential Backoff + Jitter
- Fallback Chain (DeepSeek → OpenAI)
- Request pooling e connection reuse
"""

import os
import re
import time
import random
import threading
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from enum import Enum
from openai import OpenAI
from crewai import BaseLLM

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Estados do Circuit Breaker."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered


class CircuitBreaker:
    """
    Circuit Breaker para prevenir travamentos em APIs.
    
    Estados:
    - CLOSED: Operação normal
    - OPEN: Muitas falhas, rejeita requisições
    - HALF_OPEN: Testando recuperação
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_calls: int = 3
    ):
        """
        Args:
            failure_threshold: Número de falhas para abrir circuito
            recovery_timeout: Tempo em segundos antes de tentar recuperar
            half_open_max_calls: Número de chamadas de teste em HALF_OPEN
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.lock = threading.Lock()
    
    def call(self, func, *args, **kwargs):
        """Executa função com circuit breaker."""
        with self.lock:
            # Se circuito está OPEN, verificar se pode tentar recuperar
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    logger.info(f"🔄 Circuit Breaker: Tentando recuperação (HALF_OPEN)")
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                else:
                    elapsed = time.time() - self.last_failure_time if self.last_failure_time else 0
                    remaining = self.recovery_timeout - elapsed
                    raise RuntimeError(
                        f"Circuit Breaker OPEN: API indisponível. "
                        f"Tentará novamente em {remaining:.0f}s"
                    )
        
        # Executar função
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Verifica se deve tentar recuperar."""
        if self.last_failure_time is None:
            return True
        
        elapsed = time.time() - self.last_failure_time
        return elapsed >= self.recovery_timeout
    
    def _on_success(self):
        """Registra sucesso."""
        with self.lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                logger.info(f"✅ Circuit Breaker: Sucesso {self.success_count}/{self.half_open_max_calls}")
                
                if self.success_count >= self.half_open_max_calls:
                    logger.info(f"🟢 Circuit Breaker: RECUPERADO (CLOSED)")
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
            
            elif self.state == CircuitState.CLOSED:
                # Reset failure count em sucesso
                self.failure_count = 0
    
    def _on_failure(self):
        """Registra falha."""
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.state == CircuitState.HALF_OPEN:
                logger.warning(f"🔴 Circuit Breaker: Falha durante recuperação, voltando para OPEN")
                self.state = CircuitState.OPEN
                self.success_count = 0
            
            elif self.state == CircuitState.CLOSED:
                if self.failure_count >= self.failure_threshold:
                    logger.error(
                        f"🔴 Circuit Breaker: ABERTO após {self.failure_count} falhas. "
                        f"Aguardando {self.recovery_timeout}s"
                    )
                    self.state = CircuitState.OPEN
    
    def get_state(self) -> str:
        """Retorna estado atual."""
        return self.state.value


class ComplexityAnalyzer:
    """Analisador de complexidade de tasks para escolher modelo e timeout ideal."""
    
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
        'multi-tenant', 'rbac', 'observabilidade', 'observability', 'telemetry',
        'celery', 'redis', 'websocket', 'audit', 'alembic', 'migrations',
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
            recommended_timeout = 120  # 2 minutos para tasks complexas
        elif score >= 25:
            level = 'medium'
            recommended_model = 'deepseek-reasoner' if (estimated_tokens > 4000 or score > 35) else 'deepseek-chat'
            recommended_timeout = 90  # 1.5 minutos para tasks médias
        else:
            level = 'low'
            recommended_model = 'deepseek-chat'
            recommended_timeout = 60  # 1 minuto para tasks simples
        
        return {
            'level': level,
            'score': min(score, 100),
            'estimated_tokens': estimated_tokens,
            'recommended_model': recommended_model,
            'recommended_timeout': recommended_timeout,
            'reasons': reasons,
            'keywords_found': {
                'high': high_keywords_found[:5],
                'medium': medium_keywords_found[:5]
            }
        }


class LLMRouter(BaseLLM):
    """
    Roteador inteligente de LLMs V3 com circuit breaker e adaptive timeout.
    """
    
    def __init__(
        self,
        model: str = "deepseek-chat",
        temperature: Optional[float] = 0.7,
        cooldown_seconds: int = 60,
        max_retries: int = 3,
        base_timeout: int = 60,
        auto_complexity_detection: bool = True,
        enable_circuit_breaker: bool = True
    ):
        """Inicializa o roteador de LLMs."""
        super().__init__(model=model, temperature=temperature)
        
        self.default_model = model
        self.cooldown_seconds = cooldown_seconds
        self.max_retries = max_retries
        self.base_timeout = base_timeout
        self.auto_complexity_detection = auto_complexity_detection
        self.enable_circuit_breaker = enable_circuit_breaker
        
        # Clientes com connection pooling
        self.deepseek_client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com",
            timeout=base_timeout,
            max_retries=0  # Controlamos retry manualmente
        )
        
        self.openai_client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            timeout=base_timeout,
            max_retries=0
        )
        
        # Circuit Breakers
        self.deepseek_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            half_open_max_calls=3
        ) if enable_circuit_breaker else None
        
        self.openai_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=30,
            half_open_max_calls=2
        ) if enable_circuit_breaker else None
        
        # Estado
        self.lock = threading.Lock()
        self.last_health_check = {}
        self.stats = {
            'deepseek_chat_calls': 0,
            'deepseek_chat_successes': 0,
            'deepseek_reasoner_calls': 0,
            'deepseek_reasoner_successes': 0,
            'deepseek_failures': 0,
            'deepseek_timeouts': 0,
            'deepseek_circuit_breaks': 0,
            'openai_calls': 0,
            'openai_successes': 0,
            'openai_failures': 0,
            'openai_circuit_breaks': 0,
            'total_fallbacks': 0,
            'complexity_detections': {'low': 0, 'medium': 0, 'high': 0},
            'adaptive_timeouts': {'60s': 0, '90s': 0, '120s': 0},
            'errors': []
        }
        
        logger.info("🔀 LLM Router V3 inicializado:")
        logger.info(f"   • Modelo padrão: DeepSeek ({model})")
        logger.info(f"   • Detecção automática: {'✅' if auto_complexity_detection else '❌'}")
        logger.info(f"   • Circuit Breaker: {'✅' if enable_circuit_breaker else '❌'}")
        logger.info(f"   • Adaptive Timeout: ✅ (60-120s)")
        logger.info(f"   • Max retries: {max_retries}")
    
    def _health_check(self, api_name: str) -> bool:
        """Verifica saúde da API antes de usar."""
        # Cache de 30 segundos
        if api_name in self.last_health_check:
            last_check, is_healthy = self.last_health_check[api_name]
            if time.time() - last_check < 30:
                return is_healthy
        
        # Verificar circuit breaker
        if self.enable_circuit_breaker:
            if api_name == 'deepseek' and self.deepseek_breaker.state == CircuitState.OPEN:
                logger.warning(f"🔴 Health Check: DeepSeek circuit breaker OPEN")
                self.last_health_check[api_name] = (time.time(), False)
                return False
            
            if api_name == 'openai' and self.openai_breaker.state == CircuitState.OPEN:
                logger.warning(f"🔴 Health Check: OpenAI circuit breaker OPEN")
                self.last_health_check[api_name] = (time.time(), False)
                return False
        
        # API está saudável
        self.last_health_check[api_name] = (time.time(), True)
        return True
    
    def call(
        self,
        messages: Union[str, List[Dict[str, str]]],
        tools: Optional[List[dict]] = None,
        callbacks: Optional[List[Any]] = None,
        available_functions: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Union[str, Any]:
        """Chama o LLM com circuit breaker e adaptive timeout."""
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
        
        # Log da requisição
        msg_preview = str(messages[0].get('content', ''))[:100] if messages else ''
        logger.info(f"📤 Nova requisição: {msg_preview}...")
        
        # Determinar modelo e timeout baseado em complexidade
        analysis = ComplexityAnalyzer.analyze(messages) if self.auto_complexity_detection else None
        
        if analysis:
            selected_model = analysis['recommended_model'] if not tools else 'deepseek-chat'
            adaptive_timeout = analysis['recommended_timeout']
            
            with self.lock:
                self.stats['complexity_detections'][analysis['level']] += 1
                timeout_key = f"{adaptive_timeout}s"
                if timeout_key in self.stats['adaptive_timeouts']:
                    self.stats['adaptive_timeouts'][timeout_key] += 1
            
            logger.info(f"🔍 Complexidade: {analysis['level'].upper()} (score: {analysis['score']}/100)")
            logger.info(f"   Modelo: {selected_model}, Timeout: {adaptive_timeout}s")
        else:
            selected_model = self.default_model
            adaptive_timeout = self.base_timeout
        
        # Health check e seleção de API
        deepseek_healthy = self._health_check('deepseek')
        openai_healthy = self._health_check('openai')
        
        if deepseek_healthy:
            try:
                result = self._call_deepseek(messages, tools, selected_model, adaptive_timeout)
                logger.info(f"✅ Requisição concluída (DeepSeek {selected_model})")
                return result
            except Exception as e:
                logger.warning(f"⚠️  DeepSeek falhou: {str(e)[:100]}")
                logger.info(f"🔄 Fazendo fallback para OpenAI...")
                
                if openai_healthy:
                    try:
                        result = self._call_openai(messages, tools, adaptive_timeout)
                        logger.info(f"✅ Requisição concluída com fallback (OpenAI)")
                        return result
                    except Exception as fallback_error:
                        error_msg = f"Ambas APIs falharam. DeepSeek: {str(e)[:100]}, OpenAI: {str(fallback_error)[:100]}"
                        self._record_error(error_msg)
                        logger.error(f"❌ {error_msg}")
                        raise RuntimeError(error_msg)
                else:
                    raise RuntimeError(f"DeepSeek falhou e OpenAI indisponível: {str(e)[:100]}")
        else:
            logger.info(f"⏸️  DeepSeek indisponível, usando OpenAI...")
            if openai_healthy:
                try:
                    result = self._call_openai(messages, tools, adaptive_timeout)
                    logger.info(f"✅ Requisição concluída (OpenAI)")
                    return result
                except Exception as e:
                    error_msg = f"OpenAI falhou: {str(e)[:100]}"
                    self._record_error(error_msg)
                    logger.error(f"❌ {error_msg}")
                    raise RuntimeError(error_msg)
            else:
                raise RuntimeError("Ambas APIs indisponíveis (circuit breakers OPEN)")
    
    def _call_deepseek(
        self,
        messages: List[Dict],
        tools: Optional[List] = None,
        model: str = None,
        timeout: int = 60
    ) -> str:
        """Chama DeepSeek API com circuit breaker e retry."""
        if model is None:
            model = self.default_model
        
        with self.lock:
            if model == 'deepseek-chat':
                self.stats['deepseek_chat_calls'] += 1
            else:
                self.stats['deepseek_reasoner_calls'] += 1
        
        logger.info(f"🔵 Chamando DeepSeek ({model}, timeout={timeout}s)...")
        
        # Função para executar com circuit breaker
        def _execute():
            last_error = None
            
            for attempt in range(self.max_retries):
                try:
                    start_time = time.time()
                    
                    # Atualizar timeout do cliente
                    self.deepseek_client.timeout = timeout
                    
                    payload = {
                        "model": model,
                        "messages": messages,
                        "temperature": self.temperature,
                    }
                    
                    if tools and model == 'deepseek-chat':
                        payload["tools"] = tools
                    
                    response = self.deepseek_client.chat.completions.create(**payload)
                    
                    elapsed = time.time() - start_time
                    logger.info(f"⏱️  DeepSeek respondeu em {elapsed:.1f}s")
                    
                    # Sucesso
                    with self.lock:
                        if model == 'deepseek-chat':
                            self.stats['deepseek_chat_successes'] += 1
                        else:
                            self.stats['deepseek_reasoner_successes'] += 1
                    
                    return response.choices[0].message.content
                    
                except Exception as e:
                    last_error = e
                    error_str = str(e).lower()
                    
                    # Detectar tipo de erro
                    if 'timeout' in error_str or 'timed out' in error_str:
                        with self.lock:
                            self.stats['deepseek_timeouts'] += 1
                        logger.warning(f"⏱️  DeepSeek timeout na tentativa {attempt + 1}/{self.max_retries}")
                    
                    # Retry com exponential backoff + jitter
                    if attempt < self.max_retries - 1:
                        wait_time = (2 ** attempt) + random.uniform(0, 1)  # Jitter
                        logger.info(f"⏳ Aguardando {wait_time:.1f}s antes de retry...")
                        time.sleep(wait_time)
                    else:
                        raise RuntimeError(f"DeepSeek failed: {str(e)[:100]}")
            
            raise RuntimeError(f"DeepSeek failed: {str(last_error)[:100]}")
        
        # Executar com circuit breaker
        if self.enable_circuit_breaker:
            try:
                return self.deepseek_breaker.call(_execute)
            except RuntimeError as e:
                if "Circuit Breaker OPEN" in str(e):
                    with self.lock:
                        self.stats['deepseek_circuit_breaks'] += 1
                raise e
        else:
            return _execute()
    
    def _call_openai(
        self,
        messages: List[Dict],
        tools: Optional[List] = None,
        timeout: int = 60
    ) -> str:
        """Chama OpenAI API com circuit breaker."""
        with self.lock:
            self.stats['openai_calls'] += 1
            self.stats['total_fallbacks'] += 1
        
        logger.info(f"🟢 Chamando OpenAI (gpt-4.1-mini, timeout={timeout}s)...")
        
        def _execute():
            last_error = None
            
            for attempt in range(self.max_retries):
                try:
                    start_time = time.time()
                    
                    self.openai_client.timeout = timeout
                    
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
                        wait_time = (2 ** attempt) + random.uniform(0, 1)
                        logger.warning(f"⚠️  OpenAI erro na tentativa {attempt + 1}/{self.max_retries}")
                        logger.info(f"⏳ Aguardando {wait_time:.1f}s antes de retry...")
                        time.sleep(wait_time)
                    else:
                        raise RuntimeError(f"OpenAI failed: {str(e)[:100]}")
            
            raise RuntimeError(f"OpenAI failed: {str(last_error)[:100]}")
        
        if self.enable_circuit_breaker:
            try:
                return self.openai_breaker.call(_execute)
            except RuntimeError as e:
                if "Circuit Breaker OPEN" in str(e):
                    with self.lock:
                        self.stats['openai_circuit_breaks'] += 1
                raise e
        else:
            return _execute()
    
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
            
            stats = {
                'total_calls': total_calls,
                'deepseek': {
                    'total_calls': total_deepseek,
                    'chat_calls': self.stats['deepseek_chat_calls'],
                    'chat_successes': self.stats['deepseek_chat_successes'],
                    'reasoner_calls': self.stats['deepseek_reasoner_calls'],
                    'reasoner_successes': self.stats['deepseek_reasoner_successes'],
                    'failures': self.stats['deepseek_failures'],
                    'timeouts': self.stats['deepseek_timeouts'],
                    'circuit_breaks': self.stats['deepseek_circuit_breaks'],
                    'circuit_state': self.deepseek_breaker.get_state() if self.deepseek_breaker else 'disabled',
                    'success_rate': ((self.stats['deepseek_chat_successes'] + self.stats['deepseek_reasoner_successes']) / total_deepseek * 100) 
                                   if total_deepseek > 0 else 0
                },
                'openai': {
                    'calls': self.stats['openai_calls'],
                    'successes': self.stats['openai_successes'],
                    'failures': self.stats['openai_failures'],
                    'circuit_breaks': self.stats['openai_circuit_breaks'],
                    'circuit_state': self.openai_breaker.get_state() if self.openai_breaker else 'disabled',
                    'success_rate': (self.stats['openai_successes'] / self.stats['openai_calls'] * 100)
                                   if self.stats['openai_calls'] > 0 else 0
                },
                'complexity_detections': self.stats['complexity_detections'],
                'adaptive_timeouts': self.stats['adaptive_timeouts'],
                'total_fallbacks': self.stats['total_fallbacks'],
                'recent_errors': self.stats['errors'][-5:]
            }
            
            return stats
    
    def print_stats(self):
        """Imprime estatísticas formatadas."""
        stats = self.get_stats()
        
        logger.info("=" * 80)
        logger.info("📊 ESTATÍSTICAS DO LLM ROUTER V3")
        logger.info("=" * 80)
        logger.info(f"Total de chamadas: {stats['total_calls']}")
        logger.info(f"Total de fallbacks: {stats['total_fallbacks']}")
        
        logger.info(f"\n🔵 DeepSeek:")
        logger.info(f"   Total: {stats['deepseek']['total_calls']} chamadas")
        logger.info(f"   • deepseek-chat: {stats['deepseek']['chat_calls']} ({stats['deepseek']['chat_successes']} sucessos)")
        logger.info(f"   • deepseek-reasoner: {stats['deepseek']['reasoner_calls']} ({stats['deepseek']['reasoner_successes']} sucessos)")
        logger.info(f"   Timeouts: {stats['deepseek']['timeouts']}")
        logger.info(f"   Circuit Breaks: {stats['deepseek']['circuit_breaks']}")
        logger.info(f"   Circuit State: {stats['deepseek']['circuit_state'].upper()}")
        logger.info(f"   Taxa de sucesso: {stats['deepseek']['success_rate']:.1f}%")
        
        logger.info(f"\n🟢 OpenAI:")
        logger.info(f"   Chamadas: {stats['openai']['calls']}")
        logger.info(f"   Sucessos: {stats['openai']['successes']}")
        logger.info(f"   Circuit Breaks: {stats['openai']['circuit_breaks']}")
        logger.info(f"   Circuit State: {stats['openai']['circuit_state'].upper()}")
        logger.info(f"   Taxa de sucesso: {stats['openai']['success_rate']:.1f}%")
        
        logger.info(f"\n🔍 Detecção de Complexidade:")
        logger.info(f"   • Baixa: {stats['complexity_detections']['low']}")
        logger.info(f"   • Média: {stats['complexity_detections']['medium']}")
        logger.info(f"   • Alta: {stats['complexity_detections']['high']}")
        
        logger.info(f"\n⏱️  Adaptive Timeouts:")
        logger.info(f"   • 60s: {stats['adaptive_timeouts']['60s']}")
        logger.info(f"   • 90s: {stats['adaptive_timeouts']['90s']}")
        logger.info(f"   • 120s: {stats['adaptive_timeouts']['120s']}")
        
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
    base_timeout: int = 60,
    auto_complexity_detection: bool = True,
    enable_circuit_breaker: bool = True
) -> LLMRouter:
    """Retorna instância global do LLM Router."""
    global _global_router
    
    if _global_router is None:
        _global_router = LLMRouter(
            model=model,
            temperature=temperature,
            cooldown_seconds=cooldown_seconds,
            max_retries=max_retries,
            base_timeout=base_timeout,
            auto_complexity_detection=auto_complexity_detection,
            enable_circuit_breaker=enable_circuit_breaker
        )
    
    return _global_router
