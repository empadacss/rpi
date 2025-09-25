"""
Gerenciador principal do sistema
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from core.config import Config
from core.data_collectors.abb_collector import ABBCollector
from core.data_collectors.ble_collector import BLECollector
from core.data_collectors.asic_collector import ASICCollector
from core.data_collectors.pool_collector import PoolCollector
from core.device_managers.asic_manager import ASICManager
from core.analytics.intelligent_analyzer import IntelligentAnalyzer
from core.automation.automation_controller import AutomationController
from core.automation.safety_controller import SafetyController
from core.automation.scheduler import Scheduler
from core.persistence.database import DatabaseManager
from core.persistence.report_generator import ReportGenerator
from core.notifications.notification_manager import NotificationManager
from core.websocket import WebSocketManager

logger = logging.getLogger(__name__)

@dataclass
class SystemStatus:
    """Status do sistema"""
    timestamp: datetime
    active_collectors: int
    total_miners: int
    uptime: float
    alerts_count: int
    efficiency: float
    total_hashrate: float
    total_power: float
    avg_temperature: float

class SystemManager:
    """Gerenciador principal do sistema"""
    
    def __init__(self, config: Config):
        self.config = config
        self.start_time = datetime.now()
        self.collectors = {}
        self.managers = {}
        self.tasks = []
        self.running = False
        
        # Inicializar componentes
        self._initialize_components()
        
        # Inicializar controladores de segurança e agendamento
        self.safety_controller = None
        self.scheduler = None
        self.report_generator = None
    
    def _initialize_components(self):
        """Inicializar componentes do sistema"""
        try:
            # Gerenciador de banco de dados
            self.managers['database'] = DatabaseManager(self.config)
            
            # Gerenciador de notificações
            self.managers['notifications'] = NotificationManager(self.config)
            
            # Gerenciador de ASICs
            self.managers['asic'] = ASICManager(self.config)
            
            # Analisador inteligente
            self.managers['analyzer'] = IntelligentAnalyzer(self.config)
            
            # Controlador de automação
            self.managers['automation'] = AutomationController(self.config)
            
            # Controlador de segurança
            self.safety_controller = SafetyController(self.config)
            
            # Agendador
            self.scheduler = Scheduler(self.config)
            
            # Gerador de relatórios
            self.report_generator = ReportGenerator(self.config)
            
            # Coletores de dados
            self.collectors['abb'] = ABBCollector(self.config)
            self.collectors['ble'] = BLECollector(self.config)
            self.collectors['asic'] = ASICCollector(self.config)
            self.collectors['pool'] = PoolCollector(self.config)
            
            logger.info("✅ Componentes inicializados com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar componentes: {e}")
            raise
    
    async def initialize(self):
        """Inicializar sistema"""
        try:
            logger.info("🚀 Inicializando sistema...")
            
            # Validar configuração
            if not self.config.validate_config():
                raise ValueError("Configuração inválida")
            
            # Inicializar banco de dados
            await self.managers['database'].initialize()
            
            # Inicializar gerenciadores
            for name, manager in self.managers.items():
                if hasattr(manager, 'initialize'):
                    await manager.initialize()
                logger.info(f"✅ {name} inicializado")
            
            # Inicializar controladores especiais
            if self.safety_controller:
                await self.safety_controller.initialize()
                logger.info("✅ Controlador de segurança inicializado")
            
            if self.scheduler:
                await self.scheduler.initialize()
                logger.info("✅ Agendador inicializado")
            
            if self.report_generator:
                await self.report_generator.initialize()
                logger.info("✅ Gerador de relatórios inicializado")
            
            # Inicializar coletores
            for name, collector in self.collectors.items():
                if hasattr(collector, 'initialize'):
                    await collector.initialize()
                logger.info(f"✅ {name} coletor inicializado")
            
            self.running = True
            logger.info("✅ Sistema inicializado com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar sistema: {e}")
            raise
    
    async def start_data_collection(self):
        """Iniciar coleta de dados"""
        try:
            logger.info("📊 Iniciando coleta de dados...")
            
            for name, collector in self.collectors.items():
                task = asyncio.create_task(collector.start_collection())
                self.tasks.append(task)
                logger.info(f"✅ Coleta de {name} iniciada")
            
            logger.info("✅ Coleta de dados iniciada com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar coleta de dados: {e}")
            raise
    
    async def start_intelligent_analysis(self):
        """Iniciar análise inteligente"""
        try:
            logger.info("🧠 Iniciando análise inteligente...")
            
            analyzer = self.managers['analyzer']
            task = asyncio.create_task(analyzer.start_analysis())
            self.tasks.append(task)
            
            logger.info("✅ Análise inteligente iniciada")
            
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar análise inteligente: {e}")
            raise
    
    async def start_automation(self):
        """Iniciar automação"""
        try:
            logger.info("🤖 Iniciando automação...")
            
            automation = self.managers['automation']
            task = asyncio.create_task(automation.start_automation())
            self.tasks.append(task)
            
            logger.info("✅ Automação iniciada")
            
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar automação: {e}")
            raise
    
    async def get_status(self) -> SystemStatus:
        """Obter status do sistema"""
        try:
            uptime = (datetime.now() - self.start_time).total_seconds()
            
            # Obter dados dos coletores
            active_collectors = sum(1 for collector in self.collectors.values() 
                                  if hasattr(collector, 'is_active') and collector.is_active())
            
            # Obter dados dos ASICs
            asic_manager = self.managers['asic']
            total_miners = await asic_manager.get_total_miners()
            total_hashrate = await asic_manager.get_total_hashrate()
            total_power = await asic_manager.get_total_power()
            avg_temperature = await asic_manager.get_avg_temperature()
            
            # Obter eficiência
            efficiency = await self._calculate_efficiency()
            
            # Obter alertas
            alerts_count = await self.managers['notifications'].get_active_alerts_count()
            
            return SystemStatus(
                timestamp=datetime.now(),
                active_collectors=active_collectors,
                total_miners=total_miners,
                uptime=uptime,
                alerts_count=alerts_count,
                efficiency=efficiency,
                total_hashrate=total_hashrate,
                total_power=total_power,
                avg_temperature=avg_temperature
            )
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter status: {e}")
            return SystemStatus(
                timestamp=datetime.now(),
                active_collectors=0,
                total_miners=0,
                uptime=0,
                alerts_count=0,
                efficiency=0,
                total_hashrate=0,
                total_power=0,
                avg_temperature=0
            )
    
    async def get_realtime_data(self) -> Dict[str, Any]:
        """Obter dados em tempo real"""
        try:
            data = {}
            
            # Dados dos coletores
            for name, collector in self.collectors.items():
                if hasattr(collector, 'get_latest_data'):
                    data[name] = await collector.get_latest_data()
            
            # Dados dos ASICs
            asic_manager = self.managers['asic']
            data['asic'] = await asic_manager.get_realtime_data()
            
            # Dados de análise
            analyzer = self.managers['analyzer']
            data['analysis'] = await analyzer.get_latest_analysis()
            
            return data
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter dados em tempo real: {e}")
            return {}
    
    async def get_dashboard_overview(self) -> Dict[str, Any]:
        """Obter visão geral do dashboard"""
        try:
            status = await self.get_status()
            
            return {
                "timestamp": status.timestamp.isoformat(),
                "system_status": "healthy" if status.active_collectors > 0 else "unhealthy",
                "active_collectors": status.active_collectors,
                "total_miners": status.total_miners,
                "total_hashrate": status.total_hashrate,
                "total_power": status.total_power,
                "efficiency": status.efficiency,
                "avg_temperature": status.avg_temperature,
                "alerts_count": status.alerts_count,
                "uptime": status.uptime
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter overview do dashboard: {e}")
            return {"error": str(e)}
    
    async def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Obter alertas ativos"""
        try:
            notification_manager = self.managers['notifications']
            return await notification_manager.get_active_alerts()
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter alertas: {e}")
            return []
    
    async def sleep_all_asics(self) -> Dict[str, Any]:
        """Colocar todos os ASICs em modo sleep"""
        try:
            asic_manager = self.managers['asic']
            result = await asic_manager.sleep_all()
            
            # Enviar notificação
            await self.managers['notifications'].send_alert(
                "ASIC Control",
                "Todos os ASICs foram colocados em modo sleep",
                "info"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro ao colocar ASICs em sleep: {e}")
            return {"error": str(e)}
    
    async def resume_all_asics(self) -> Dict[str, Any]:
        """Retomar todos os ASICs"""
        try:
            asic_manager = self.managers['asic']
            result = await asic_manager.resume_all()
            
            # Enviar notificação
            await self.managers['notifications'].send_alert(
                "ASIC Control",
                "Todos os ASICs foram retomados",
                "info"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro ao retomar ASICs: {e}")
            return {"error": str(e)}
    
    async def get_financial_report(self) -> Dict[str, Any]:
        """Obter relatório financeiro"""
        try:
            # Implementar lógica de relatório financeiro
            return {
                "timestamp": datetime.now().isoformat(),
                "total_revenue": 0.0,
                "total_costs": 0.0,
                "profit": 0.0,
                "roi": 0.0,
                "break_even_days": 0
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter relatório financeiro: {e}")
            return {"error": str(e)}
    
    async def get_operational_report(self) -> Dict[str, Any]:
        """Obter relatório operacional"""
        try:
            status = await self.get_status()
            
            return {
                "timestamp": status.timestamp.isoformat(),
                "uptime": status.uptime,
                "efficiency": status.efficiency,
                "total_hashrate": status.total_hashrate,
                "total_power": status.total_power,
                "avg_temperature": status.avg_temperature,
                "alerts_count": status.alerts_count
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter relatório operacional: {e}")
            return {"error": str(e)}
    
    async def _calculate_efficiency(self) -> float:
        """Calcular eficiência do sistema"""
        try:
            asic_manager = self.managers['asic']
            total_hashrate = await asic_manager.get_total_hashrate()
            total_power = await asic_manager.get_total_power()
            
            if total_power > 0:
                return total_hashrate / total_power
            return 0.0
            
        except Exception as e:
            logger.error(f"❌ Erro ao calcular eficiência: {e}")
            return 0.0
    
    async def shutdown(self):
        """Parar sistema"""
        try:
            logger.info("🛑 Parando sistema...")
            
            self.running = False
            
            # Parar tarefas
            for task in self.tasks:
                task.cancel()
            
            # Aguardar tarefas terminarem
            await asyncio.gather(*self.tasks, return_exceptions=True)
            
            # Parar coletores
            for collector in self.collectors.values():
                if hasattr(collector, 'stop'):
                    await collector.stop()
            
            # Parar gerenciadores
            for manager in self.managers.values():
                if hasattr(manager, 'shutdown'):
                    await manager.shutdown()
            
            logger.info("✅ Sistema parado com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro ao parar sistema: {e}")
