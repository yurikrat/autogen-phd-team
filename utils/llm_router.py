#!/usr/bin/env python3
"""
LLM Router - Roteamento inteligente entre OpenAI e DeepSeek com fallback automático.

Funcionalidades:
- Roteamento automático entre DeepSeek (principal) e OpenAI (fallback)
- Detecção automática de complexidade para escolher modelo ideal
- Tratamento de timeout e rate limit
- Recuperação automática após cooldown
- Monitoramento de uso e estatísticas
- Compatível com CrewAI BaseLLM
"""

import os
import re
import time
import threading
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from openai import OpenAI
from crewai import BaseLLM


class ComplexityAnalyzer:
    """
    Analisador de complexidade de tasks para escolher modelo ideal.
    """
    
    # Palavras-chave que indicam alta complexidade
    HIGH_COMPLEXITY_KEYWORDS = [
        # Escopo amplo
        'completo', 'complete', 'sistema', 'system', 'aplicação', 'application',
        'projeto', 'project', 'arquitetura', 'architecture', 'infraestrutura', 'infrastructure',
        
        # Multi-componentes
        'multi', 'múltiplos', 'multiple', 'vários', 'various', 'todos', 'all',
        'frontend e backend', 'full stack', 'fullstack', 'end-to-end', 'e2e',
        
        # Integração complexa
        'integração', 'integration', 'microsserviço', 'microservice', 'microsserviço',
        'orquestração', 'orchestration', 'pipeline', 'workflow',
        'gateway', 'pagamento', 'payment', 'autenticação', 'authentication',
        
        # Análise profunda
        'análise completa', 'deep analysis', 'troubleshooting', 'debug',
        'investigação', 'investigation', 'diagnóstico', 'diagnostic',
        
        # Documentação extensa
        'documentação completa', 'complete documentation', 'manual', 'guia completo',
        'especificação', 'specification', 'detalhado', 'detailed',
        
        # Refatoração grande
        'refatorar tudo', 'refactor all', 'reescrever', 'rewrite', 'migrar', 'migrate',
        
        # Logs e dados extensos
        'todos os logs', 'all logs', 'histórico completo', 'full history',
        'análise de logs', 'log analysis',
        
        # Deploy e CI/CD
        'ci/cd', 'docker', 'kubernetes', 'deploy', 'deployment',
    ]
    
    # Palavras-chave que indicam média complexidade
    MEDIUM_COMPLEXITY_KEYWORDS = [
        'api', 'endpoint', 'serviço', 'service', 'módulo', 'module',
        'componente', 'component', 'feature', 'funcionalidade',
        'crud', 'rest', 'graphql', 'banco de dados', 'database',
    ]
    
    # Padrões que indicam alta complexidade
    HIGH_COMPLEXITY_PATTERNS = [
        r'\b\d+\+?\s*(arquivos|files|componentes|components|módulos|modules)\b',
        r'\b(criar|create|desenvolver|develop|implementar|implement)\s+(um|uma|a)\s+sistema\b',
        r'\b(backend|frontend)\s+(e|and)\s+(frontend|backend)\b',
        r'\b(com|with)\s+\d+\+?\s+(funcionalidades|features|endpoints)\b',
    ]
    
    @staticmethod
    def analyze(messages: Union[str, List[Dict[str, str]]]) -> Dict[str, Any]:
        """
        Analisa a complexidade de uma task.
        
        Args:
            messages: String ou lista de mensagens
            
        Returns:
            Dict com análise de complexidade:
            {
                'level': 'low' | 'medium' | 'high',
                'score': 0-100,
                'estimated_tokens': int,
                'recommended_model': 'deepseek-chat' | 'deepseek-reasoner',
                'reasons': List[str]
            }
        """
        # Converter para texto único
        if isinstance(messages, str):
            text = messages
        elif isinstance(messages, list):
            text = ' '.join([msg.get('content', '') for msg in messages if isinstance(msg, dict)])
        else:
            text = str(messages)
        
        text_lower = text.lower()
        
        # Inicializar análise
        score = 0
        reasons = []
        
        # 1. Análise de tamanho do input (15-40 pontos)
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
        
        # 2. Palavras-chave de alta complexidade (8 pontos cada, max 50)
        high_keywords_found = []
        for keyword in ComplexityAnalyzer.HIGH_COMPLEXITY_KEYWORDS:
            if keyword in text_lower:
                high_keywords_found.append(keyword)
        
        keyword_score = min(len(high_keywords_found) * 8, 50)
        score += keyword_score
        if high_keywords_found:
            reasons.append(f"Palavras de alta complexidade ({len(high_keywords_found)}): {', '.join(high_keywords_found[:3])}")
        
        # 3. Palavras-chave de média complexidade (4 pontos cada, max 20)
        medium_keywords_found = []
        for keyword in ComplexityAnalyzer.MEDIUM_COMPLEXITY_KEYWORDS:
            if keyword in text_lower:
                medium_keywords_found.append(keyword)
        
        medium_score = min(len(medium_keywords_found) * 4, 20)
        score += medium_score
        if medium_keywords_found:
            reasons.append(f"Palavras de média complexidade ({len(medium_keywords_found)}): {', '.join(medium_keywords_found[:3])}")
        
        # 4. Padrões de alta complexidade (15 pontos cada, max 45)
        patterns_found = []
        for pattern in ComplexityAnalyzer.HIGH_COMPLEXITY_PATTERNS:
            if re.search(pattern, text_lower):
                patterns_found.append(pattern)
        
        pattern_score = min(len(patterns_found) * 15, 45)
        score += pattern_score
        if patterns_found:
            reasons.append(f"Padrões complexos detectados ({len(patterns_found)})")
        
        # 5. Estimativa de tokens de output necessários
        # Baseado em heurísticas
        estimated_tokens = 1000  # Base
        
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
        
        # Adicionar baseado no tamanho do input
        estimated_tokens += char_count // 2
        
        # 6. Determinar nível de complexidade
        if score >= 45:
            level = 'high'
            recommended_model = 'deepseek-reasoner'
        elif score >= 25:
            level = 'medium'
            # Média complexidade: usar reasoner se estimativa > 4K tokens OU score > 35
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
    Roteador inteligente de LLMs com fallback automático e detecção de complexidade.
    
    Estratégia:
    1. Analisa complexidade da task automaticamente
    2. Escolhe modelo ideal (deepseek-chat ou deepseek-reasoner)
    3. DeepSeek como principal (mais barato)
    4. OpenAI como fallback (mais confiável)
    5. Fallback automático em caso de erro 429, 503, timeout
    6. Recuperação automática após cooldown
    """
    
    def __init__(
        self,
        model: str = "deepseek-chat",
        temperature: Optional[float] = 0.7,
        cooldown_seconds: int = 60,
        max_retries: int = 2,
        timeout: int = 120,
        auto_complexity_detection: bool = True,
        complexity_threshold: int = 30
    ):
        """
        Inicializa o roteador de LLMs.
        
        Args:
            model: Nome do modelo padrão (usado para DeepSeek)
            temperature: Temperatura para geração
            cooldown_seconds: Tempo de espera após falha antes de tentar DeepSeek novamente
            max_retries: Número máximo de tentativas por API
            timeout: Timeout em segundos para requisições
            auto_complexity_detection: Se True, detecta complexidade automaticamente
            complexity_threshold: Score mínimo para considerar alta complexidade
        """
        # OBRIGATÓRIO: Chamar super().__init__() com model e temperature
        super().__init__(model=model, temperature=temperature)
        
        # Configurações
        self.default_model = model
        self.cooldown_seconds = cooldown_seconds
        self.max_retries = max_retries
        self.timeout = timeout
        self.auto_complexity_detection = auto_complexity_detection
        self.complexity_threshold = complexity_threshold
        
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
            'deepseek_chat_calls': 0,
            'deepseek_chat_successes': 0,
            'deepseek_reasoner_calls': 0,
            'deepseek_reasoner_successes': 0,
            'deepseek_failures': 0,
            'openai_calls': 0,
            'openai_successes': 0,
            'openai_failures': 0,
            'total_fallbacks': 0,
            'complexity_detections': {
                'low': 0,
                'medium': 0,
                'high': 0
            },
            'errors': []
        }
        
        print("🔀 LLM Router inicializado:")
        print(f"   • Modelo padrão: DeepSeek ({model})")
        print(f"   • Detecção automática: {'✅ Ativada' if auto_complexity_detection else '❌ Desativada'}")
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
        
        # Determinar modelo baseado em complexidade e tools
        selected_model = self._select_model(messages, tools)
        
        # Determinar qual API usar
        use_deepseek = self._should_use_deepseek()
        
        if use_deepseek:
            # Tentar DeepSeek primeiro
            try:
                return self._call_deepseek(messages, tools, selected_model)
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
    
    def _select_model(self, messages: List[Dict], tools: Optional[List] = None) -> str:
        """
        Seleciona o modelo ideal baseado em complexidade e tools.
        
        Args:
            messages: Lista de mensagens
            tools: Lista de tools (se presente, força deepseek-chat)
            
        Returns:
            Nome do modelo ('deepseek-chat' ou 'deepseek-reasoner')
        """
        # Se tem tools, SEMPRE usar deepseek-chat
        # (deepseek-reasoner não suporta function calling)
        if tools:
            return 'deepseek-chat'
        
        # Se detecção automática desativada, usar modelo padrão
        if not self.auto_complexity_detection:
            return self.default_model
        
        # Analisar complexidade
        analysis = ComplexityAnalyzer.analyze(messages)
        
        # Registrar detecção
        with self.lock:
            self.stats['complexity_detections'][analysis['level']] += 1
        
        # Log da análise
        print(f"\n   🔍 Análise de Complexidade:")
        print(f"      • Nível: {analysis['level'].upper()}")
        print(f"      • Score: {analysis['score']}/100")
        print(f"      • Tokens estimados: {analysis['estimated_tokens']}")
        print(f"      • Modelo recomendado: {analysis['recommended_model']}")
        if analysis['reasons']:
            print(f"      • Razões: {', '.join(analysis['reasons'][:2])}")
        
        return analysis['recommended_model']
    
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
    
    def _call_deepseek(self, messages: List[Dict], tools: Optional[List] = None, model: str = None) -> str:
        """Chama DeepSeek API com retry."""
        if model is None:
            model = self.default_model
        
        # Registrar chamada
        with self.lock:
            if model == 'deepseek-chat':
                self.stats['deepseek_chat_calls'] += 1
            else:
                self.stats['deepseek_reasoner_calls'] += 1
        
        print(f"   🔵 Usando DeepSeek ({model})...")
        
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                # Preparar payload
                payload = {
                    "model": model,
                    "messages": messages,
                    "temperature": self.temperature,
                }
                
                # Adicionar tools se fornecido E modelo suportar
                if tools and model == 'deepseek-chat':
                    payload["tools"] = tools
                
                # Fazer chamada
                response = self.deepseek_client.chat.completions.create(**payload)
                
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
        
        print(f"   🟢 Usando OpenAI (gpt-4.1-mini)...")
        
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
        
        print("\n" + "=" * 80)
        print("📊 ESTATÍSTICAS DO LLM ROUTER")
        print("=" * 80)
        print(f"Total de chamadas: {stats['total_calls']}")
        print(f"Total de fallbacks: {stats['total_fallbacks']}")
        
        print(f"\n🔵 DeepSeek:")
        print(f"   Total: {stats['deepseek']['total_calls']} chamadas")
        print(f"   • deepseek-chat: {stats['deepseek']['chat_calls']} ({stats['deepseek']['chat_successes']} sucessos)")
        print(f"   • deepseek-reasoner: {stats['deepseek']['reasoner_calls']} ({stats['deepseek']['reasoner_successes']} sucessos)")
        print(f"   Falhas: {stats['deepseek']['failures']}")
        print(f"   Taxa de sucesso: {stats['deepseek']['success_rate']:.1f}%")
        
        print(f"\n🟢 OpenAI:")
        print(f"   Chamadas: {stats['openai']['calls']}")
        print(f"   Sucessos: {stats['openai']['successes']}")
        print(f"   Falhas: {stats['openai']['failures']}")
        print(f"   Taxa de sucesso: {stats['openai']['success_rate']:.1f}%")
        
        print(f"\n🔍 Detecção de Complexidade:")
        print(f"   • Baixa: {stats['complexity_detections']['low']}")
        print(f"   • Média: {stats['complexity_detections']['medium']}")
        print(f"   • Alta: {stats['complexity_detections']['high']}")
        
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
    timeout: int = 120,
    auto_complexity_detection: bool = True,
    complexity_threshold: int = 30
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
            complexity_threshold=complexity_threshold
        )
    
    return _global_router


if __name__ == "__main__":
    # Teste do LLM Router com detecção de complexidade
    print("🧪 Testando LLM Router com Detecção de Complexidade...\n")
    
    router = get_llm_router()
    
    # Teste 1: Task simples (deve usar deepseek-chat)
    print("\n" + "=" * 80)
    print("Teste 1: Task Simples")
    print("=" * 80)
    try:
        response = router.call("Crie uma função Python que soma dois números.")
        print(f"✅ Resposta: {response[:100]}\n")
    except Exception as e:
        print(f"❌ Erro: {e}\n")
    
    # Teste 2: Task média (pode usar chat ou reasoner)
    print("\n" + "=" * 80)
    print("Teste 2: Task Média")
    print("=" * 80)
    try:
        response = router.call("Crie uma API REST completa com CRUD de usuários usando FastAPI.")
        print(f"✅ Resposta: {response[:100]}\n")
    except Exception as e:
        print(f"❌ Erro: {e}\n")
    
    # Teste 3: Task complexa (deve usar deepseek-reasoner)
    print("\n" + "=" * 80)
    print("Teste 3: Task Complexa")
    print("=" * 80)
    try:
        response = router.call("""
        Crie um sistema completo de e-commerce com:
        - Backend em Python com FastAPI
        - Frontend em React
        - Banco de dados PostgreSQL
        - Autenticação JWT
        - Sistema de pagamento
        - Carrinho de compras
        - Painel administrativo
        - Documentação completa
        - Testes unitários e de integração
        - Docker e docker-compose
        - CI/CD com GitHub Actions
        """)
        print(f"✅ Resposta: {response[:100]}\n")
    except Exception as e:
        print(f"❌ Erro: {e}\n")
    
    # Estatísticas
    router.print_stats()
