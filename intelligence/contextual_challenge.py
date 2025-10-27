"""
Sistema de Provocação Contextual Inteligente.
Analisa o contexto real e gera desafios específicos, não genéricos.
"""

from typing import Dict, List, Any
import json


class ContextualChallengeSystem:
    """
    Sistema que analisa o contexto da conversa e gera desafios específicos.
    Funciona como um time humano real, não com perguntas pré-prontas.
    """
    
    def __init__(self):
        self.conversation_history = []
        self.artifacts_created = []
        self.challenges_issued = []
        self.improvements_made = []
    
    def analyze_context(self, message: str, role: str, artifacts: List[Dict]) -> Dict[str, Any]:
        """
        Analisa o contexto atual para identificar oportunidades de desafio.
        
        Args:
            message: Mensagem do agente
            role: Papel do agente
            artifacts: Artefatos criados até agora
        
        Returns:
            Análise contextual com oportunidades de melhoria
        """
        analysis = {
            "has_technical_decision": False,
            "has_security_concern": False,
            "has_performance_issue": False,
            "has_scalability_concern": False,
            "missing_tests": False,
            "missing_documentation": False,
            "missing_error_handling": False,
            "opportunities": []
        }
        
        msg_lower = message.lower()
        
        # Detectar decisões técnicas
        tech_keywords = ["implementar", "criar", "usar", "escolher", "decidir", "arquitetura"]
        if any(kw in msg_lower for kw in tech_keywords):
            analysis["has_technical_decision"] = True
            analysis["opportunities"].append({
                "type": "technical_review",
                "reason": "Decisão técnica detectada - precisa de revisão de arquitetura"
            })
        
        # Detectar preocupações de segurança
        security_keywords = ["api", "autenticação", "senha", "token", "dados", "usuário", "login"]
        if any(kw in msg_lower for kw in security_keywords):
            analysis["has_security_concern"] = True
            analysis["opportunities"].append({
                "type": "security_review",
                "reason": "Componente sensível detectado - precisa de análise de segurança"
            })
        
        # Detectar possíveis problemas de performance
        perf_keywords = ["loop", "query", "busca", "lista", "todos", "processar"]
        if any(kw in msg_lower for kw in perf_keywords):
            analysis["has_performance_issue"] = True
            analysis["opportunities"].append({
                "type": "performance_review",
                "reason": "Operação potencialmente custosa - precisa de análise de performance"
            })
        
        # Detectar preocupações de escalabilidade
        scale_keywords = ["múltiplos", "vários", "grande", "crescer", "escalar"]
        if any(kw in msg_lower for kw in scale_keywords):
            analysis["has_scalability_concern"] = True
            analysis["opportunities"].append({
                "type": "scalability_review",
                "reason": "Cenário de escala detectado - precisa de análise de escalabilidade"
            })
        
        # Verificar artefatos criados
        has_code = any(a.get("kind") in ["python", "javascript", "code"] for a in artifacts)
        has_tests = any("test" in a.get("name", "").lower() for a in artifacts)
        has_docs = any(a.get("kind") == "markdown" for a in artifacts)
        
        if has_code and not has_tests:
            analysis["missing_tests"] = True
            analysis["opportunities"].append({
                "type": "testing_gap",
                "reason": "Código criado sem testes - precisa de cobertura de testes"
            })
        
        if has_code and not has_docs:
            analysis["missing_documentation"] = True
            analysis["opportunities"].append({
                "type": "documentation_gap",
                "reason": "Código criado sem documentação - precisa de docs"
            })
        
        # Detectar falta de tratamento de erros
        if "try" not in msg_lower and "except" not in msg_lower and "error" not in msg_lower:
            if any(kw in msg_lower for kw in ["api", "request", "database", "file"]):
                analysis["missing_error_handling"] = True
                analysis["opportunities"].append({
                    "type": "error_handling_gap",
                    "reason": "Operação sem tratamento de erros - precisa de error handling"
                })
        
        return analysis
    
    def generate_contextual_challenge(
        self,
        from_role: str,
        to_role: str,
        context_analysis: Dict[str, Any],
        message_content: str
    ) -> str:
        """
        Gera um desafio específico baseado no contexto real.
        
        Args:
            from_role: Papel que desafia
            to_role: Papel desafiado
            context_analysis: Análise do contexto
            message_content: Conteúdo da mensagem original
        
        Returns:
            Desafio contextual específico
        """
        opportunities = context_analysis.get("opportunities", [])
        
        if not opportunities:
            return ""
        
        # Mapear papéis para tipos de desafios que fazem sentido
        role_expertise = {
            "Tech_Architect": ["technical_review", "scalability_review"],
            "SecOps": ["security_review"],
            "Performance_Engineer": ["performance_review"],
            "QA_Engineer": ["testing_gap", "error_handling_gap"],
            "Docs_Specialist": ["documentation_gap"],
        }
        
        # Encontrar oportunidades relevantes para o papel
        relevant_opportunities = [
            opp for opp in opportunities
            if opp["type"] in role_expertise.get(from_role, [])
        ]
        
        if not relevant_opportunities:
            return ""
        
        # Pegar a primeira oportunidade relevante
        opportunity = relevant_opportunities[0]
        
        # Gerar desafio específico baseado no tipo e contexto
        challenge_templates = {
            "technical_review": self._generate_technical_challenge,
            "security_review": self._generate_security_challenge,
            "performance_review": self._generate_performance_challenge,
            "scalability_review": self._generate_scalability_challenge,
            "testing_gap": self._generate_testing_challenge,
            "documentation_gap": self._generate_documentation_challenge,
            "error_handling_gap": self._generate_error_handling_challenge,
        }
        
        generator = challenge_templates.get(opportunity["type"])
        if generator:
            challenge = generator(message_content, opportunity)
            
            self.challenges_issued.append({
                "from": from_role,
                "to": to_role,
                "type": opportunity["type"],
                "challenge": challenge,
                "context": message_content[:200]
            })
            
            return f"🎯 **{from_role} → {to_role}:** {challenge}"
        
        return ""
    
    def _generate_technical_challenge(self, message: str, opportunity: Dict) -> str:
        """Gera desafio técnico específico baseado no contexto."""
        msg_lower = message.lower()
        
        if "api" in msg_lower:
            return "Você considerou versionamento da API (v1, v2)? Como vai lidar com breaking changes sem quebrar clientes existentes?"
        elif "banco" in msg_lower or "database" in msg_lower:
            return "Essa escolha de banco suporta transações ACID? Como vai garantir consistência em caso de falha parcial?"
        elif "cache" in msg_lower:
            return "Qual estratégia de invalidação de cache? Como evitar cache stampede em cenários de alta concorrência?"
        elif "fila" in msg_lower or "queue" in msg_lower:
            return "Como garantir idempotência no processamento de mensagens? E se a mesma mensagem for processada duas vezes?"
        else:
            return "Essa decisão técnica considera os trade-offs de complexidade vs. benefício? Existe uma solução mais simples que atende 80% dos casos?"
    
    def _generate_security_challenge(self, message: str, opportunity: Dict) -> str:
        """Gera desafio de segurança específico baseado no contexto."""
        msg_lower = message.lower()
        
        if "autenticação" in msg_lower or "login" in msg_lower:
            return "Você implementou rate limiting para prevenir brute force? Como está protegendo contra credential stuffing?"
        elif "token" in msg_lower or "jwt" in msg_lower:
            return "Os tokens têm tempo de expiração curto? Como está gerenciando revogação de tokens comprometidos?"
        elif "senha" in msg_lower or "password" in msg_lower:
            return "Está usando hashing adequado (bcrypt, Argon2)? Qual o salt factor? Como previne timing attacks?"
        elif "dados" in msg_lower or "data" in msg_lower:
            return "Dados sensíveis estão sendo criptografados em repouso e em trânsito? Como está garantindo LGPD/GDPR compliance?"
        else:
            return "Essa implementação foi analisada contra OWASP Top 10? Quais controles de segurança estão em camadas (defense in depth)?"
    
    def _generate_performance_challenge(self, message: str, opportunity: Dict) -> str:
        """Gera desafio de performance específico baseado no contexto."""
        msg_lower = message.lower()
        
        if "loop" in msg_lower or "for" in msg_lower:
            return "Qual a complexidade dessa operação? Se processar 1M de registros, quanto tempo vai levar? Pode ser otimizado com batch processing?"
        elif "query" in msg_lower or "busca" in msg_lower:
            return "Essa query tem índices adequados? Qual o explain plan? Como se comporta com 10M de registros?"
        elif "api" in msg_lower:
            return "Qual a latência p99 esperada? Implementou timeout e circuit breaker? Como vai se comportar sob carga?"
        else:
            return "Essa operação pode ser assíncrona? Existe oportunidade de paralelização ou cache?"
    
    def _generate_scalability_challenge(self, message: str, opportunity: Dict) -> str:
        """Gera desafio de escalabilidade específico baseado no contexto."""
        msg_lower = message.lower()
        
        if "usuário" in msg_lower or "user" in msg_lower:
            return "Essa solução escala horizontalmente? Se tiver 100x mais usuários simultâneos, o que vai quebrar primeiro?"
        elif "dados" in msg_lower or "data" in msg_lower:
            return "Como vai particionar/shardar os dados quando crescer? Pensou em estratégia de archiving para dados antigos?"
        else:
            return "Essa arquitetura é stateless? Pode adicionar mais instâncias sem problemas? Como funciona o load balancing?"
    
    def _generate_testing_challenge(self, message: str, opportunity: Dict) -> str:
        """Gera desafio de testes específico baseado no contexto."""
        return "Onde estão os testes para esse código? Preciso ver testes unitários, de integração e edge cases. Como vai validar que funciona?"
    
    def _generate_documentation_challenge(self, message: str, opportunity: Dict) -> str:
        """Gera desafio de documentação específico baseado no contexto."""
        return "Cadê a documentação? Outro desenvolvedor consegue entender e manter isso em 6 meses? Preciso de docs claros com exemplos."
    
    def _generate_error_handling_challenge(self, message: str, opportunity: Dict) -> str:
        """Gera desafio de tratamento de erros específico baseado no contexto."""
        return "E se essa operação falhar? Como vai tratar erros? Preciso ver try/except, logging adequado e estratégia de retry/fallback."
    
    def should_challenge(self, from_role: str, message: str, artifacts: List[Dict]) -> bool:
        """
        Decide se deve gerar um desafio baseado no contexto.
        
        Args:
            from_role: Papel que potencialmente vai desafiar
            message: Mensagem atual
            artifacts: Artefatos criados
        
        Returns:
            True se deve desafiar
        """
        analysis = self.analyze_context(message, from_role, artifacts)
        
        # Mapear papéis para tipos de análise relevantes
        role_concerns = {
            "Tech_Architect": ["has_technical_decision", "has_scalability_concern"],
            "SecOps": ["has_security_concern"],
            "Performance_Engineer": ["has_performance_issue"],
            "QA_Engineer": ["missing_tests", "missing_error_handling"],
            "Docs_Specialist": ["missing_documentation"],
        }
        
        concerns = role_concerns.get(from_role, [])
        return any(analysis.get(concern, False) for concern in concerns)


# Instância global
_challenge_system = None

def get_challenge_system() -> ContextualChallengeSystem:
    """Retorna instância singleton do sistema de desafios."""
    global _challenge_system
    if _challenge_system is None:
        _challenge_system = ContextualChallengeSystem()
    return _challenge_system

