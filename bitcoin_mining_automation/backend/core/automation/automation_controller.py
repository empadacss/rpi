"""
Controlador de automação para mineração de Bitcoin
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class AutomationAction(Enum):
    """Ações de automação"""
    SLEEP_ASICS = "sleep_asics"
    RESUME_ASICS = "resume_asics"
    INCREASE_FAN_SPEED = "increase_fan_speed"
    DECREASE_FAN_SPEED = "decrease_fan_speed"
    ACTIVATE_COOLING = "activate_cooling"
    DEACTIVATE_COOLING = "deactivate_cooling"
    SEND_ALERT = "send_alert"
    OPTIMIZE_SETTINGS = "optimize_settings"

@dataclass
class AutomationRule:
    """Regra de automação"""
    name: str
    condition: str
    action: AutomationAction
    parameters: Dict[str, Any]
    enabled: bool = True
    cooldown: int = 300  # segundos
    last_triggered: Optional[datetime] = None

class AutomationController:
    """Controlador de automação"""
    
    def __init__(self, config):
        self.config = config
        self.running = False
        self.rules = []
        self.action_history = []
        self.max_history = 1000
        
        # Configurações
        self.check_interval = 10  # segundos
        self.thresholds = config.get_thresholds()
        
        # Inicializar regras padrão
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """Inicializar regras padrão de automação"""
        try:
            # Regra de temperatura crítica
            self.rules.append(AutomationRule(
                name="temperatura_critica",
                condition="temperature > temp_critical",
                action=AutomationAction.SLEEP_ASICS,
                parameters={"reason": "Temperatura crítica detectada"},
                cooldown=600  # 10 minutos
            ))
            
            # Regra de temperatura alta
            self.rules.append(AutomationRule(
                name="temperatura_alta",
                condition="temperature > temp_max",
                action=AutomationAction.INCREASE_FAN_SPEED,
                parameters={"fan_speed": 100},
                cooldown=300  # 5 minutos
            ))
            
            # Regra de eficiência baixa
            self.rules.append(AutomationRule(
                name="eficiencia_baixa",
                condition="efficiency < efficiency_min",
                action=AutomationAction.OPTIMIZE_SETTINGS,
                parameters={"optimization_type": "performance"},
                cooldown=1800  # 30 minutos
            ))
            
            # Regra de desconexão de minerador
            self.rules.append(AutomationRule(
                name="minerador_desconectado",
                condition="miner_status == 'offline'",
                action=AutomationAction.SEND_ALERT,
                parameters={"alert_type": "miner_offline"},
                cooldown=60  # 1 minuto
            ))
            
            # Regra de ativação de refrigeração
            self.rules.append(AutomationRule(
                name="ativar_refrigeracao",
                condition="temperature > temp_max and humidity > humidity_max",
                action=AutomationAction.ACTIVATE_COOLING,
                parameters={"cooling_level": "high"},
                cooldown=300  # 5 minutos
            ))
            
            # Regra de desativação de refrigeração
            self.rules.append(AutomationRule(
                name="desativar_refrigeracao",
                condition="temperature < temp_max - 5 and humidity < humidity_max - 10",
                action=AutomationAction.DEACTIVATE_COOLING,
                parameters={"cooling_level": "off"},
                cooldown=600  # 10 minutos
            ))
            
            logger.info(f"✅ {len(self.rules)} regras de automação inicializadas")
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar regras de automação: {e}")
    
    async def initialize(self):
        """Inicializar controlador"""
        try:
            logger.info("🤖 Inicializando controlador de automação")
            logger.info("✅ Controlador de automação inicializado com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar controlador: {e}")
            raise
    
    async def start_automation(self):
        """Iniciar automação"""
        try:
            logger.info("🤖 Iniciando automação")
            self.running = True
            
            while self.running:
                try:
                    # Verificar regras
                    await self._check_rules()
                    
                    # Aguardar próximo ciclo
                    await asyncio.sleep(self.check_interval)
                    
                except Exception as e:
                    logger.error(f"❌ Erro na automação: {e}")
                    await asyncio.sleep(5)  # Aguardar antes de tentar novamente
                    
        except Exception as e:
            logger.error(f"❌ Erro na automação: {e}")
        finally:
            self.running = False
            logger.info("🛑 Automação parada")
    
    async def _check_rules(self):
        """Verificar regras de automação"""
        try:
            # Obter dados atuais do sistema (simulado)
            current_data = await self._get_current_system_data()
            
            if not current_data:
                return
            
            # Verificar cada regra
            for rule in self.rules:
                if not rule.enabled:
                    continue
                
                # Verificar cooldown
                if rule.last_triggered:
                    time_since_last = datetime.now() - rule.last_triggered
                    if time_since_last.total_seconds() < rule.cooldown:
                        continue
                
                # Verificar condição
                if await self._evaluate_condition(rule.condition, current_data):
                    # Executar ação
                    await self._execute_action(rule, current_data)
                    
                    # Atualizar timestamp
                    rule.last_triggered = datetime.now()
                    
                    logger.info(f"🤖 Regra '{rule.name}' executada")
            
        except Exception as e:
            logger.error(f"❌ Erro ao verificar regras: {e}")
    
    async def _evaluate_condition(self, condition: str, data: Dict[str, Any]) -> bool:
        """Avaliar condição da regra"""
        try:
            # Substituir variáveis na condição
            condition = condition.replace('temp_critical', str(self.thresholds['temp_critical']))
            condition = condition.replace('temp_max', str(self.thresholds['temp_max']))
            condition = condition.replace('humidity_max', str(self.thresholds['humidity_max']))
            condition = condition.replace('efficiency_min', str(self.thresholds['efficiency_min']))
            
            # Avaliar condição
            # Em produção, usar um parser de expressões mais robusto
            if 'temperature >' in condition:
                temp_value = data.get('temperature', 0)
                threshold = float(condition.split('>')[1].strip())
                return temp_value > threshold
            
            elif 'efficiency <' in condition:
                efficiency = data.get('efficiency', 1)
                threshold = float(condition.split('<')[1].strip())
                return efficiency < threshold
            
            elif 'miner_status ==' in condition:
                status = condition.split('==')[1].strip().strip("'\"")
                return data.get('miner_status') == status
            
            elif 'humidity >' in condition:
                humidity = data.get('humidity', 0)
                threshold = float(condition.split('>')[1].strip())
                return humidity > threshold
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Erro ao avaliar condição '{condition}': {e}")
            return False
    
    async def _execute_action(self, rule: AutomationRule, data: Dict[str, Any]):
        """Executar ação da regra"""
        try:
            action = rule.action
            parameters = rule.parameters
            
            if action == AutomationAction.SLEEP_ASICS:
                await self._sleep_all_asics(parameters)
            
            elif action == AutomationAction.RESUME_ASICS:
                await self._resume_all_asics(parameters)
            
            elif action == AutomationAction.INCREASE_FAN_SPEED:
                await self._increase_fan_speed(parameters)
            
            elif action == AutomationAction.DECREASE_FAN_SPEED:
                await self._decrease_fan_speed(parameters)
            
            elif action == AutomationAction.ACTIVATE_COOLING:
                await self._activate_cooling(parameters)
            
            elif action == AutomationAction.DEACTIVATE_COOLING:
                await self._deactivate_cooling(parameters)
            
            elif action == AutomationAction.SEND_ALERT:
                await self._send_alert(parameters, data)
            
            elif action == AutomationAction.OPTIMIZE_SETTINGS:
                await self._optimize_settings(parameters)
            
            # Registrar ação no histórico
            self._record_action(rule, data)
            
        except Exception as e:
            logger.error(f"❌ Erro ao executar ação {rule.action}: {e}")
    
    async def _sleep_all_asics(self, parameters: Dict[str, Any]):
        """Colocar todos os ASICs em modo sleep"""
        try:
            logger.info("😴 Colocando todos os ASICs em modo sleep")
            
            # Em produção, integrar com o gerenciador de ASICs
            # await self.asic_manager.sleep_all()
            
            logger.info("✅ Todos os ASICs colocados em modo sleep")
            
        except Exception as e:
            logger.error(f"❌ Erro ao colocar ASICs em sleep: {e}")
    
    async def _resume_all_asics(self, parameters: Dict[str, Any]):
        """Retomar todos os ASICs"""
        try:
            logger.info("▶️ Retomando todos os ASICs")
            
            # Em produção, integrar com o gerenciador de ASICs
            # await self.asic_manager.resume_all()
            
            logger.info("✅ Todos os ASICs retomados")
            
        except Exception as e:
            logger.error(f"❌ Erro ao retomar ASICs: {e}")
    
    async def _increase_fan_speed(self, parameters: Dict[str, Any]):
        """Aumentar velocidade dos ventiladores"""
        try:
            fan_speed = parameters.get('fan_speed', 100)
            logger.info(f"🌀 Aumentando velocidade dos ventiladores para {fan_speed}%")
            
            # Em produção, integrar com controle de ventiladores
            # await self.fan_controller.set_speed(fan_speed)
            
            logger.info("✅ Velocidade dos ventiladores aumentada")
            
        except Exception as e:
            logger.error(f"❌ Erro ao aumentar velocidade dos ventiladores: {e}")
    
    async def _decrease_fan_speed(self, parameters: Dict[str, Any]):
        """Diminuir velocidade dos ventiladores"""
        try:
            fan_speed = parameters.get('fan_speed', 50)
            logger.info(f"🌀 Diminuindo velocidade dos ventiladores para {fan_speed}%")
            
            # Em produção, integrar com controle de ventiladores
            # await self.fan_controller.set_speed(fan_speed)
            
            logger.info("✅ Velocidade dos ventiladores diminuída")
            
        except Exception as e:
            logger.error(f"❌ Erro ao diminuir velocidade dos ventiladores: {e}")
    
    async def _activate_cooling(self, parameters: Dict[str, Any]):
        """Ativar sistema de refrigeração"""
        try:
            cooling_level = parameters.get('cooling_level', 'high')
            logger.info(f"❄️ Ativando sistema de refrigeração (nível: {cooling_level})")
            
            # Em produção, integrar com controle de refrigeração
            # await self.cooling_controller.activate(cooling_level)
            
            logger.info("✅ Sistema de refrigeração ativado")
            
        except Exception as e:
            logger.error(f"❌ Erro ao ativar refrigeração: {e}")
    
    async def _deactivate_cooling(self, parameters: Dict[str, Any]):
        """Desativar sistema de refrigeração"""
        try:
            logger.info("❄️ Desativando sistema de refrigeração")
            
            # Em produção, integrar com controle de refrigeração
            # await self.cooling_controller.deactivate()
            
            logger.info("✅ Sistema de refrigeração desativado")
            
        except Exception as e:
            logger.error(f"❌ Erro ao desativar refrigeração: {e}")
    
    async def _send_alert(self, parameters: Dict[str, Any], data: Dict[str, Any]):
        """Enviar alerta"""
        try:
            alert_type = parameters.get('alert_type', 'general')
            message = f"Alerta automático: {alert_type}"
            
            logger.warning(f"🚨 {message}")
            
            # Em produção, integrar com sistema de notificações
            # await self.notification_manager.send_alert(alert_type, message, data)
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar alerta: {e}")
    
    async def _optimize_settings(self, parameters: Dict[str, Any]):
        """Otimizar configurações"""
        try:
            optimization_type = parameters.get('optimization_type', 'performance')
            logger.info(f"⚙️ Otimizando configurações (tipo: {optimization_type})")
            
            # Em produção, integrar com sistema de otimização
            # await self.optimization_engine.optimize(optimization_type)
            
            logger.info("✅ Configurações otimizadas")
            
        except Exception as e:
            logger.error(f"❌ Erro ao otimizar configurações: {e}")
    
    def _record_action(self, rule: AutomationRule, data: Dict[str, Any]):
        """Registrar ação no histórico"""
        try:
            action_record = {
                'timestamp': datetime.now(),
                'rule_name': rule.name,
                'action': rule.action.value,
                'parameters': rule.parameters,
                'data_snapshot': data
            }
            
            self.action_history.append(action_record)
            
            # Manter apenas os últimos N registros
            if len(self.action_history) > self.max_history:
                self.action_history = self.action_history[-self.max_history:]
            
        except Exception as e:
            logger.error(f"❌ Erro ao registrar ação: {e}")
    
    async def _get_current_system_data(self) -> Dict[str, Any]:
        """Obter dados atuais do sistema (simulado)"""
        # Em produção, isso viria do sistema de coleta de dados
        return {
            'temperature': 70.0,
            'humidity': 60.0,
            'efficiency': 0.85,
            'miner_status': 'active',
            'total_miners': 10,
            'active_miners': 9
        }
    
    async def add_rule(self, rule: AutomationRule):
        """Adicionar nova regra"""
        try:
            self.rules.append(rule)
            logger.info(f"✅ Regra '{rule.name}' adicionada")
            
        except Exception as e:
            logger.error(f"❌ Erro ao adicionar regra: {e}")
    
    async def remove_rule(self, rule_name: str):
        """Remover regra"""
        try:
            self.rules = [r for r in self.rules if r.name != rule_name]
            logger.info(f"✅ Regra '{rule_name}' removida")
            
        except Exception as e:
            logger.error(f"❌ Erro ao remover regra: {e}")
    
    async def enable_rule(self, rule_name: str):
        """Habilitar regra"""
        try:
            for rule in self.rules:
                if rule.name == rule_name:
                    rule.enabled = True
                    logger.info(f"✅ Regra '{rule_name}' habilitada")
                    return
            
            logger.warning(f"⚠️ Regra '{rule_name}' não encontrada")
            
        except Exception as e:
            logger.error(f"❌ Erro ao habilitar regra: {e}")
    
    async def disable_rule(self, rule_name: str):
        """Desabilitar regra"""
        try:
            for rule in self.rules:
                if rule.name == rule_name:
                    rule.enabled = False
                    logger.info(f"✅ Regra '{rule_name}' desabilitada")
                    return
            
            logger.warning(f"⚠️ Regra '{rule_name}' não encontrada")
            
        except Exception as e:
            logger.error(f"❌ Erro ao desabilitar regra: {e}")
    
    async def get_rules(self) -> List[Dict[str, Any]]:
        """Obter lista de regras"""
        try:
            return [
                {
                    'name': rule.name,
                    'condition': rule.condition,
                    'action': rule.action.value,
                    'parameters': rule.parameters,
                    'enabled': rule.enabled,
                    'cooldown': rule.cooldown,
                    'last_triggered': rule.last_triggered.isoformat() if rule.last_triggered else None
                }
                for rule in self.rules
            ]
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter regras: {e}")
            return []
    
    async def get_action_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Obter histórico de ações"""
        try:
            return self.action_history[-limit:]
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter histórico: {e}")
            return []
    
    def is_active(self) -> bool:
        """Verificar se o controlador está ativo"""
        return self.running
    
    async def shutdown(self):
        """Parar controlador"""
        try:
            logger.info("🛑 Parando controlador de automação")
            self.running = False
            logger.info("✅ Controlador de automação parado")
                
        except Exception as e:
            logger.error(f"❌ Erro ao parar controlador: {e}")


