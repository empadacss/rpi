"""
Sistema de análise inteligente com LLM
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class IntelligentAnalyzer:
    """Analisador inteligente com LLM"""
    
    def __init__(self, config):
        self.config = config
        self.running = False
        self.llm_config = config.get_llm_config()
        self.analysis_cache = {}
        self.alert_history = []
        
        # Configurações de análise
        self.analysis_interval = 30  # segundos
        self.cache_ttl = 300  # 5 minutos
        self.max_alert_history = 1000
        
        # Inicializar cliente LLM
        self._initialize_llm_client()
    
    def _initialize_llm_client(self):
        """Inicializar cliente LLM"""
        try:
            if self.llm_config['mode'] == 'local':
                self.llm_client = LocalLLMClient(self.llm_config)
            elif self.llm_config['mode'] == 'remote':
                self.llm_client = RemoteLLMClient(self.llm_config)
            else:
                raise ValueError(f"Modo LLM inválido: {self.llm_config['mode']}")
            
            logger.info(f"✅ Cliente LLM inicializado: {self.llm_config['mode']}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar cliente LLM: {e}")
            raise
    
    async def initialize(self):
        """Inicializar analisador"""
        try:
            logger.info("🧠 Inicializando analisador inteligente")
            
            # Testar conexão com LLM
            if await self._test_llm_connection():
                logger.info("✅ Analisador inteligente inicializado com sucesso")
            else:
                logger.warning("⚠️ LLM não disponível, analisador funcionará em modo limitado")
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar analisador: {e}")
            raise
    
    async def start_analysis(self):
        """Iniciar análise inteligente"""
        try:
            logger.info("🧠 Iniciando análise inteligente")
            self.running = True
            
            while self.running:
                try:
                    # Realizar análise
                    await self._perform_analysis()
                    
                    # Aguardar próximo ciclo
                    await asyncio.sleep(self.analysis_interval)
                    
                except Exception as e:
                    logger.error(f"❌ Erro na análise inteligente: {e}")
                    await asyncio.sleep(10)  # Aguardar antes de tentar novamente
                    
        except Exception as e:
            logger.error(f"❌ Erro na análise inteligente: {e}")
        finally:
            self.running = False
            logger.info("🛑 Análise inteligente parada")
    
    async def _perform_analysis(self):
        """Realizar análise dos dados"""
        try:
            # Obter dados recentes (simulado - em produção viria do sistema)
            recent_data = await self._get_recent_data()
            
            if not recent_data:
                return
            
            # Analisar dados operacionais
            operational_analysis = await self._analyze_operational_data(recent_data)
            
            # Analisar dados de performance
            performance_analysis = await self._analyze_performance_data(recent_data)
            
            # Analisar dados de temperatura
            temperature_analysis = await self._analyze_temperature_data(recent_data)
            
            # Analisar dados financeiros
            financial_analysis = await self._analyze_financial_data(recent_data)
            
            # Combinar análises
            combined_analysis = {
                'timestamp': datetime.now(),
                'operational': operational_analysis,
                'performance': performance_analysis,
                'temperature': temperature_analysis,
                'financial': financial_analysis,
                'recommendations': await self._generate_recommendations(
                    operational_analysis,
                    performance_analysis,
                    temperature_analysis,
                    financial_analysis
                )
            }
            
            # Armazenar análise
            self.analysis_cache['latest'] = combined_analysis
            
            # Verificar alertas
            await self._check_alerts(combined_analysis)
            
            logger.debug(f"🧠 Análise concluída: {len(combined_analysis.get('recommendations', []))} recomendações")
            
        except Exception as e:
            logger.error(f"❌ Erro na análise: {e}")
    
    async def _analyze_operational_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analisar dados operacionais"""
        try:
            prompt = f"""
            Analise os seguintes dados operacionais de mineração de Bitcoin:
            
            Dados do Sistema:
            - Total de mineradores: {data.get('total_miners', 0)}
            - Mineradores ativos: {data.get('active_miners', 0)}
            - Hashrate total: {data.get('total_hashrate', 0)} TH/s
            - Consumo total de energia: {data.get('total_power', 0)} W
            - Eficiência: {data.get('efficiency', 0):.2f} TH/s/W
            
            Dados dos Mineradores:
            {json.dumps(data.get('miners', []), indent=2)}
            
            Forneça uma análise detalhada incluindo:
            1. Status geral da operação
            2. Identificação de problemas
            3. Eficiência operacional
            4. Recomendações de otimização
            5. Previsões de performance
            """
            
            analysis = await self.llm_client.analyze(prompt)
            return self._parse_analysis(analysis, 'operational')
            
        except Exception as e:
            logger.error(f"❌ Erro na análise operacional: {e}")
            return {'error': str(e)}
    
    async def _analyze_performance_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analisar dados de performance"""
        try:
            prompt = f"""
            Analise a performance dos mineradores de Bitcoin:
            
            Métricas de Performance:
            - Hashrate total: {data.get('total_hashrate', 0)} TH/s
            - Eficiência média: {data.get('efficiency', 0):.2f} TH/s/W
            - Temperatura média: {data.get('avg_temperature', 0)}°C
            - Uptime médio: {data.get('avg_uptime', 0)}%
            
            Dados por Minerador:
            {json.dumps(data.get('miners', []), indent=2)}
            
            Forneça uma análise de performance incluindo:
            1. Comparação com benchmarks
            2. Identificação de mineradores com baixa performance
            3. Análise de tendências
            4. Recomendações de otimização
            5. Previsões de performance futura
            """
            
            analysis = await self.llm_client.analyze(prompt)
            return self._parse_analysis(analysis, 'performance')
            
        except Exception as e:
            logger.error(f"❌ Erro na análise de performance: {e}")
            return {'error': str(e)}
    
    async def _analyze_temperature_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analisar dados de temperatura"""
        try:
            prompt = f"""
            Analise os dados de temperatura dos mineradores:
            
            Temperatura Média: {data.get('avg_temperature', 0)}°C
            Temperatura Máxima: {data.get('max_temperature', 0)}°C
            Temperatura Mínima: {data.get('min_temperature', 0)}°C
            
            Dados de Temperatura por Minerador:
            {json.dumps([{k: v for k, v in m.items() if 'temp' in k.lower()} for m in data.get('miners', [])], indent=2)}
            
            Forneça uma análise térmica incluindo:
            1. Status térmico geral
            2. Identificação de hotspots
            3. Análise de risco de superaquecimento
            4. Recomendações de controle térmico
            5. Previsões de temperatura
            """
            
            analysis = await self.llm_client.analyze(prompt)
            return self._parse_analysis(analysis, 'temperature')
            
        except Exception as e:
            logger.error(f"❌ Erro na análise de temperatura: {e}")
            return {'error': str(e)}
    
    async def _analyze_financial_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analisar dados financeiros"""
        try:
            prompt = f"""
            Analise os dados financeiros da operação de mineração:
            
            Métricas Financeiras:
            - Hashrate total: {data.get('total_hashrate', 0)} TH/s
            - Consumo de energia: {data.get('total_power', 0)} W
            - Eficiência: {data.get('efficiency', 0):.2f} TH/s/W
            - Custo de energia estimado: R$ {data.get('energy_cost', 0):.2f}/kWh
            
            Forneça uma análise financeira incluindo:
            1. ROI atual e projetado
            2. Análise de custos operacionais
            3. Comparação com benchmarks de mercado
            4. Recomendações de otimização financeira
            5. Previsões de rentabilidade
            """
            
            analysis = await self.llm_client.analyze(prompt)
            return self._parse_analysis(analysis, 'financial')
            
        except Exception as e:
            logger.error(f"❌ Erro na análise financeira: {e}")
            return {'error': str(e)}
    
    async def _generate_recommendations(self, operational: Dict, performance: Dict, 
                                      temperature: Dict, financial: Dict) -> List[Dict[str, Any]]:
        """Gerar recomendações baseadas nas análises"""
        try:
            recommendations = []
            
            # Recomendações operacionais
            if operational.get('status') == 'warning':
                recommendations.append({
                    'type': 'operational',
                    'priority': 'high',
                    'title': 'Problema Operacional Detectado',
                    'description': operational.get('message', 'Verifique a operação'),
                    'action': 'Verificar mineradores e conexões'
                })
            
            # Recomendações de performance
            if performance.get('efficiency') < 0.8:
                recommendations.append({
                    'type': 'performance',
                    'priority': 'medium',
                    'title': 'Eficiência Baixa',
                    'description': f"Eficiência atual: {performance.get('efficiency', 0):.2f}",
                    'action': 'Otimizar configurações dos mineradores'
                })
            
            # Recomendações térmicas
            if temperature.get('status') == 'critical':
                recommendations.append({
                    'type': 'temperature',
                    'priority': 'critical',
                    'title': 'Temperatura Crítica',
                    'description': temperature.get('message', 'Temperatura muito alta'),
                    'action': 'Ativar sistema de refrigeração imediatamente'
                })
            
            # Recomendações financeiras
            if financial.get('roi') < 0.1:
                recommendations.append({
                    'type': 'financial',
                    'priority': 'low',
                    'title': 'ROI Baixo',
                    'description': f"ROI atual: {financial.get('roi', 0):.2%}",
                    'action': 'Revisar custos operacionais'
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar recomendações: {e}")
            return []
    
    async def _check_alerts(self, analysis: Dict[str, Any]):
        """Verificar alertas baseados na análise"""
        try:
            alerts = []
            
            # Verificar alertas críticos
            if analysis.get('temperature', {}).get('status') == 'critical':
                alerts.append({
                    'type': 'temperature',
                    'severity': 'critical',
                    'message': 'Temperatura crítica detectada',
                    'timestamp': datetime.now()
                })
            
            # Verificar alertas de performance
            if analysis.get('performance', {}).get('efficiency', 1) < 0.7:
                alerts.append({
                    'type': 'performance',
                    'severity': 'warning',
                    'message': 'Eficiência muito baixa',
                    'timestamp': datetime.now()
                })
            
            # Verificar alertas operacionais
            if analysis.get('operational', {}).get('status') == 'error':
                alerts.append({
                    'type': 'operational',
                    'severity': 'error',
                    'message': 'Problema operacional detectado',
                    'timestamp': datetime.now()
                })
            
            # Adicionar alertas ao histórico
            for alert in alerts:
                self.alert_history.append(alert)
                
                # Manter apenas os últimos N alertas
                if len(self.alert_history) > self.max_alert_history:
                    self.alert_history = self.alert_history[-self.max_alert_history:]
            
            # Enviar alertas se necessário
            if alerts:
                await self._send_alerts(alerts)
            
        except Exception as e:
            logger.error(f"❌ Erro ao verificar alertas: {e}")
    
    async def _send_alerts(self, alerts: List[Dict[str, Any]]):
        """Enviar alertas"""
        try:
            # Em produção, aqui seria integrado com o sistema de notificações
            for alert in alerts:
                logger.warning(f"🚨 ALERTA: {alert['type']} - {alert['message']}")
                
        except Exception as e:
            logger.error(f"❌ Erro ao enviar alertas: {e}")
    
    def _parse_analysis(self, analysis: str, analysis_type: str) -> Dict[str, Any]:
        """Parsear análise do LLM"""
        try:
            # Tentar parsear como JSON
            try:
                return json.loads(analysis)
            except json.JSONDecodeError:
                pass
            
            # Parsear como texto estruturado
            return {
                'type': analysis_type,
                'raw_analysis': analysis,
                'timestamp': datetime.now(),
                'status': 'completed'
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao parsear análise: {e}")
            return {'error': str(e)}
    
    async def _get_recent_data(self) -> Dict[str, Any]:
        """Obter dados recentes (simulado)"""
        # Em produção, isso viria do sistema de coleta de dados
        return {
            'total_miners': 10,
            'active_miners': 9,
            'total_hashrate': 100.5,
            'total_power': 10000,
            'efficiency': 0.01005,
            'avg_temperature': 65.0,
            'max_temperature': 75.0,
            'min_temperature': 55.0,
            'miners': [
                {
                    'id': f'miner_{i}',
                    'hashrate': 10.0 + i,
                    'power': 1000 + i * 100,
                    'temperature': 60 + i * 2,
                    'status': 'active' if i < 9 else 'offline'
                }
                for i in range(10)
            ]
        }
    
    async def _test_llm_connection(self) -> bool:
        """Testar conexão com LLM"""
        try:
            test_prompt = "Teste de conexão"
            response = await self.llm_client.analyze(test_prompt)
            return response is not None
        except Exception as e:
            logger.error(f"❌ Erro no teste de conexão LLM: {e}")
            return False
    
    async def get_latest_analysis(self) -> Dict[str, Any]:
        """Obter análise mais recente"""
        return self.analysis_cache.get('latest', {})
    
    async def get_recommendations(self) -> List[Dict[str, Any]]:
        """Obter recomendações ativas"""
        analysis = await self.get_latest_analysis()
        return analysis.get('recommendations', [])
    
    async def get_alerts(self) -> List[Dict[str, Any]]:
        """Obter alertas ativos"""
        return self.alert_history[-10:]  # Últimos 10 alertas
    
    def is_active(self) -> bool:
        """Verificar se o analisador está ativo"""
        return self.running
    
    async def shutdown(self):
        """Parar analisador"""
        try:
            logger.info("🛑 Parando analisador inteligente")
            self.running = False
            logger.info("✅ Analisador inteligente parado")
                
        except Exception as e:
            logger.error(f"❌ Erro ao parar analisador: {e}")

class LocalLLMClient:
    """Cliente LLM local"""
    
    def __init__(self, config):
        self.config = config
        self.endpoint = config['endpoint']
    
    async def analyze(self, prompt: str) -> str:
        """Analisar prompt com LLM local"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.endpoint}/api/generate",
                    json={"prompt": prompt},
                    timeout=30
                )
                response.raise_for_status()
                return response.text
        except Exception as e:
            logger.error(f"❌ Erro na análise LLM local: {e}")
            return f"Erro na análise: {e}"

class RemoteLLMClient:
    """Cliente LLM remoto"""
    
    def __init__(self, config):
        self.config = config
        self.openai_key = config.get('openai_api_key')
        self.anthropic_key = config.get('anthropic_api_key')
    
    async def analyze(self, prompt: str) -> str:
        """Analisar prompt com LLM remoto"""
        try:
            if self.openai_key:
                return await self._analyze_with_openai(prompt)
            elif self.anthropic_key:
                return await self._analyze_with_anthropic(prompt)
            else:
                raise ValueError("Nenhuma chave de API configurada")
        except Exception as e:
            logger.error(f"❌ Erro na análise LLM remoto: {e}")
            return f"Erro na análise: {e}"
    
    async def _analyze_with_openai(self, prompt: str) -> str:
        """Analisar com OpenAI"""
        # Implementar integração com OpenAI
        return "Análise OpenAI (não implementada)"
    
    async def _analyze_with_anthropic(self, prompt: str) -> str:
        """Analisar com Anthropic"""
        # Implementar integração com Anthropic
        return "Análise Anthropic (não implementada)"


