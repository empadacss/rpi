"""
Controlador de segurança para mineração de Bitcoin
Baseado no script original com automações de segurança
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class SafetyAction(Enum):
    """Ações de segurança"""
    SLEEP_ASICS = "sleep_asics"
    RESUME_ASICS = "resume_asics"
    ADJUST_FAN_SPEED = "adjust_fan_speed"
    SEND_ALERT = "send_alert"
    LOG_EVENT = "log_event"

class SafetyLevel(Enum):
    """Níveis de segurança"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

@dataclass
class SafetyEvent:
    """Evento de segurança"""
    timestamp: datetime
    level: SafetyLevel
    message: str
    action: SafetyAction
    parameters: Dict[str, Any]
    resolved: bool = False
    resolved_at: Optional[datetime] = None

class SafetyController:
    """Controlador de segurança"""
    
    def __init__(self, config):
        self.config = config
        self.running = False
        self.safety_events = []
        self.callbacks = []
        
        # Configurações de segurança
        self.thresholds = {
            'humidity_critical': 90.0,  # Umidade crítica
            'dew_point_diff_critical': 4.0,  # Diferença temperatura - ponto de orvalho
            'inverter_not_run_timeout': 30,  # Timeout para inversor não em RUN
            'connection_timeout': 30,  # Timeout de conexão
            'fan_speed_humidity': 20,  # Velocidade do ventilador para umidade alta
            'fan_speed_dew_point': 10  # Velocidade do ventilador para ponto de orvalho
        }
        
        # Estado dos dispositivos
        self.device_states = {
            'inverter_running': False,
            'asics_mining': False,
            'last_inverter_check': None,
            'last_asic_check': None,
            'sensor_data': {}
        }
        
        # Histórico de eventos
        self.max_events = 1000
        
    async def initialize(self):
        """Inicializar controlador de segurança"""
        try:
            logger.info("🛡️ Inicializando controlador de segurança")
            logger.info("✅ Controlador de segurança inicializado com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar controlador de segurança: {e}")
            raise
    
    async def start_safety_monitoring(self):
        """Iniciar monitoramento de segurança"""
        try:
            logger.info("🛡️ Iniciando monitoramento de segurança")
            self.running = True
            
            while self.running:
                try:
                    # Verificar regras de segurança
                    await self._check_safety_rules()
                    
                    # Aguardar próximo ciclo
                    await asyncio.sleep(5)  # Verificar a cada 5 segundos
                    
                except Exception as e:
                    logger.error(f"❌ Erro no monitoramento de segurança: {e}")
                    await asyncio.sleep(10)  # Aguardar antes de tentar novamente
                    
        except Exception as e:
            logger.error(f"❌ Erro no monitoramento de segurança: {e}")
        finally:
            self.running = False
            logger.info("🛑 Monitoramento de segurança parado")
    
    async def _check_safety_rules(self):
        """Verificar regras de segurança"""
        try:
            # 1. Verificar se inversor não está em RUN com ASICs minerando
            await self._check_inverter_safety()
            
            # 2. Verificar umidade crítica
            await self._check_humidity_safety()
            
            # 3. Verificar ponto de orvalho
            await self._check_dew_point_safety()
            
            # 4. Verificar timeouts de conexão
            await self._check_connection_timeouts()
            
        except Exception as e:
            logger.error(f"❌ Erro ao verificar regras de segurança: {e}")
    
    async def _check_inverter_safety(self):
        """Verificar segurança do inversor"""
        try:
            inverter_running = self.device_states.get('inverter_running', False)
            asics_mining = self.device_states.get('asics_mining', False)
            
            # Se inversor não está em RUN e ASICs estão minerando
            if not inverter_running and asics_mining:
                await self._trigger_safety_event(
                    SafetyLevel.CRITICAL,
                    "Inversor não está em RUN com ASICs minerando! Colocando ASICs em sleep.",
                    SafetyAction.SLEEP_ASICS,
                    {"reason": "Inversor não em RUN"}
                )
            
        except Exception as e:
            logger.error(f"❌ Erro na verificação de segurança do inversor: {e}")
    
    async def _check_humidity_safety(self):
        """Verificar segurança de umidade"""
        try:
            sensor_data = self.device_states.get('sensor_data', {})
            
            for mac, data in sensor_data.items():
                humidity = data.get('humidity')
                if humidity is not None and humidity >= self.thresholds['humidity_critical']:
                    await self._trigger_safety_event(
                        SafetyLevel.WARNING,
                        f"Umidade crítica detectada: {humidity:.1f}% (sensor {mac}). Ajustando ventilador para {self.thresholds['fan_speed_humidity']}%.",
                        SafetyAction.ADJUST_FAN_SPEED,
                        {
                            "fan_speed": self.thresholds['fan_speed_humidity'],
                            "reason": f"Umidade crítica: {humidity:.1f}%",
                            "sensor": mac
                        }
                    )
            
        except Exception as e:
            logger.error(f"❌ Erro na verificação de segurança de umidade: {e}")
    
    async def _check_dew_point_safety(self):
        """Verificar segurança do ponto de orvalho"""
        try:
            sensor_data = self.device_states.get('sensor_data', {})
            
            for mac, data in sensor_data.items():
                temperature = data.get('temperature')
                humidity = data.get('humidity')
                
                if temperature is not None and humidity is not None:
                    dew_point = self._calculate_dew_point(temperature, humidity)
                    if dew_point is not None:
                        diff = temperature - dew_point
                        if diff < self.thresholds['dew_point_diff_critical']:
                            await self._trigger_safety_event(
                                SafetyLevel.WARNING,
                                f"Diferença T-DP crítica: {diff:.1f}°C (sensor {mac}). Ajustando ventilador para {self.thresholds['fan_speed_dew_point']}%.",
                                SafetyAction.ADJUST_FAN_SPEED,
                                {
                                    "fan_speed": self.thresholds['fan_speed_dew_point'],
                                    "reason": f"Diferença T-DP crítica: {diff:.1f}°C",
                                    "sensor": mac,
                                    "temperature": temperature,
                                    "dew_point": dew_point
                                }
                            )
            
        except Exception as e:
            logger.error(f"❌ Erro na verificação de segurança do ponto de orvalho: {e}")
    
    async def _check_connection_timeouts(self):
        """Verificar timeouts de conexão"""
        try:
            current_time = datetime.now()
            timeout_threshold = self.thresholds['connection_timeout']
            
            # Verificar timeout do inversor
            last_inverter_check = self.device_states.get('last_inverter_check')
            if last_inverter_check:
                time_since_check = (current_time - last_inverter_check).total_seconds()
                if time_since_check > timeout_threshold:
                    await self._trigger_safety_event(
                        SafetyLevel.CRITICAL,
                        f"Inversor sem resposta há {time_since_check:.0f} segundos!",
                        SafetyAction.SEND_ALERT,
                        {
                            "device": "inverter",
                            "timeout": time_since_check,
                            "threshold": timeout_threshold
                        }
                    )
            
            # Verificar timeout dos ASICs
            last_asic_check = self.device_states.get('last_asic_check')
            if last_asic_check:
                time_since_check = (current_time - last_asic_check).total_seconds()
                if time_since_check > timeout_threshold:
                    await self._trigger_safety_event(
                        SafetyLevel.WARNING,
                        f"ASICs sem resposta há {time_since_check:.0f} segundos!",
                        SafetyAction.SEND_ALERT,
                        {
                            "device": "asics",
                            "timeout": time_since_check,
                            "threshold": timeout_threshold
                        }
                    )
            
        except Exception as e:
            logger.error(f"❌ Erro na verificação de timeouts: {e}")
    
    def _calculate_dew_point(self, temperature: float, humidity: float) -> Optional[float]:
        """Calcular ponto de orvalho"""
        try:
            import math
            a = 17.27
            b = 237.7
            gamma = math.log(humidity / 100.0) + (a * temperature) / (b + temperature)
            return (b * gamma) / (a - gamma)
        except Exception:
            return None
    
    async def _trigger_safety_event(self, level: SafetyLevel, message: str, 
                                  action: SafetyAction, parameters: Dict[str, Any]):
        """Disparar evento de segurança"""
        try:
            event = SafetyEvent(
                timestamp=datetime.now(),
                level=level,
                message=message,
                action=action,
                parameters=parameters
            )
            
            # Adicionar ao histórico
            self.safety_events.append(event)
            if len(self.safety_events) > self.max_events:
                self.safety_events = self.safety_events[-self.max_events:]
            
            # Executar ação
            await self._execute_safety_action(event)
            
            # Executar callbacks
            for callback in self.callbacks:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"❌ Erro em callback de segurança: {e}")
            
            # Log do evento
            log_level = {
                SafetyLevel.INFO: logging.INFO,
                SafetyLevel.WARNING: logging.WARNING,
                SafetyLevel.CRITICAL: logging.ERROR,
                SafetyLevel.EMERGENCY: logging.CRITICAL
            }
            
            logger.log(log_level[level], f"🛡️ SEGURANÇA [{level.value.upper()}] {message}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao disparar evento de segurança: {e}")
    
    async def _execute_safety_action(self, event: SafetyEvent):
        """Executar ação de segurança"""
        try:
            if event.action == SafetyAction.SLEEP_ASICS:
                await self._sleep_all_asics(event.parameters)
            
            elif event.action == SafetyAction.RESUME_ASICS:
                await self._resume_all_asics(event.parameters)
            
            elif event.action == SafetyAction.ADJUST_FAN_SPEED:
                await self._adjust_fan_speed(event.parameters)
            
            elif event.action == SafetyAction.SEND_ALERT:
                await self._send_safety_alert(event)
            
            elif event.action == SafetyAction.LOG_EVENT:
                await self._log_safety_event(event)
            
        except Exception as e:
            logger.error(f"❌ Erro ao executar ação de segurança: {e}")
    
    async def _sleep_all_asics(self, parameters: Dict[str, Any]):
        """Colocar todos os ASICs em sleep"""
        try:
            logger.info("😴 Colocando todos os ASICs em sleep por segurança")
            # Em produção, integrar com o gerenciador de ASICs
            # await self.asic_manager.sleep_all()
            
        except Exception as e:
            logger.error(f"❌ Erro ao colocar ASICs em sleep: {e}")
    
    async def _resume_all_asics(self, parameters: Dict[str, Any]):
        """Retomar todos os ASICs"""
        try:
            logger.info("▶️ Retomando todos os ASICs")
            # Em produção, integrar com o gerenciador de ASICs
            # await self.asic_manager.resume_all()
            
        except Exception as e:
            logger.error(f"❌ Erro ao retomar ASICs: {e}")
    
    async def _adjust_fan_speed(self, parameters: Dict[str, Any]):
        """Ajustar velocidade do ventilador"""
        try:
            fan_speed = parameters.get('fan_speed', 50)
            reason = parameters.get('reason', 'Ajuste de segurança')
            
            logger.info(f"🌀 Ajustando ventilador para {fan_speed}% - {reason}")
            # Em produção, integrar com controle de ventiladores
            # await self.fan_controller.set_speed(fan_speed)
            
        except Exception as e:
            logger.error(f"❌ Erro ao ajustar velocidade do ventilador: {e}")
    
    async def _send_safety_alert(self, event: SafetyEvent):
        """Enviar alerta de segurança"""
        try:
            logger.warning(f"🚨 ALERTA DE SEGURANÇA: {event.message}")
            # Em produção, integrar com sistema de notificações
            # await self.notification_manager.send_alert(
            #     "safety", event.message, event.level.value
            # )
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar alerta de segurança: {e}")
    
    async def _log_safety_event(self, event: SafetyEvent):
        """Registrar evento de segurança"""
        try:
            # Em produção, integrar com sistema de logs
            logger.info(f"📝 Evento de segurança registrado: {event.message}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao registrar evento de segurança: {e}")
    
    def update_device_state(self, device: str, state: Any):
        """Atualizar estado de um dispositivo"""
        try:
            if device == 'inverter':
                self.device_states['inverter_running'] = state
                self.device_states['last_inverter_check'] = datetime.now()
            
            elif device == 'asics':
                self.device_states['asics_mining'] = state
                self.device_states['last_asic_check'] = datetime.now()
            
            elif device == 'sensor_data':
                self.device_states['sensor_data'] = state
            
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar estado do dispositivo {device}: {e}")
    
    def add_callback(self, callback: Callable[[SafetyEvent], None]):
        """Adicionar callback para eventos de segurança"""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[SafetyEvent], None]):
        """Remover callback"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def get_safety_events(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Obter eventos de segurança"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            return [
                {
                    'timestamp': event.timestamp.isoformat(),
                    'level': event.level.value,
                    'message': event.message,
                    'action': event.action.value,
                    'parameters': event.parameters,
                    'resolved': event.resolved,
                    'resolved_at': event.resolved_at.isoformat() if event.resolved_at else None
                }
                for event in self.safety_events
                if event.timestamp > cutoff_time
            ]
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter eventos de segurança: {e}")
            return []
    
    def get_safety_statistics(self) -> Dict[str, Any]:
        """Obter estatísticas de segurança"""
        try:
            if not self.safety_events:
                return {}
            
            # Estatísticas dos últimos 24 horas
            recent_events = [
                event for event in self.safety_events
                if event.timestamp > datetime.now() - timedelta(hours=24)
            ]
            
            stats = {
                'total_events': len(recent_events),
                'critical_events': len([e for e in recent_events if e.level == SafetyLevel.CRITICAL]),
                'warning_events': len([e for e in recent_events if e.level == SafetyLevel.WARNING]),
                'info_events': len([e for e in recent_events if e.level == SafetyLevel.INFO]),
                'emergency_events': len([e for e in recent_events if e.level == SafetyLevel.EMERGENCY]),
                'resolved_events': len([e for e in recent_events if e.resolved]),
                'unresolved_events': len([e for e in recent_events if not e.resolved])
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Erro ao calcular estatísticas de segurança: {e}")
            return {}
    
    def is_active(self) -> bool:
        """Verificar se o controlador está ativo"""
        return self.running
    
    async def stop(self):
        """Parar controlador de segurança"""
        try:
            logger.info("🛑 Parando controlador de segurança")
            self.running = False
            logger.info("✅ Controlador de segurança parado")
                
        except Exception as e:
            logger.error(f"❌ Erro ao parar controlador de segurança: {e}")


