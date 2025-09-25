"""
Sistema de agendamento e rotinas de automação
Baseado no script original com funcionalidades de schedule
"""

import asyncio
import logging
import json
import schedule
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)

class ScheduleAction(Enum):
    """Ações de agendamento"""
    SLEEP_ASICS = "sleep"
    RESUME_ASICS = "resume"
    ADJUST_FAN_SPEED = "adjust_fan_speed"
    START_EXHAUST = "start_exhaust"
    STOP_EXHAUST = "stop_exhaust"
    SEND_ALERT = "send_alert"
    CUSTOM_COMMAND = "custom_command"

class ScheduleFrequency(Enum):
    """Frequências de agendamento"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"

@dataclass
class ScheduleRule:
    """Regra de agendamento"""
    id: str
    name: str
    description: str
    action: ScheduleAction
    parameters: Dict[str, Any]
    frequency: ScheduleFrequency
    time: str  # HH:MM format
    days: List[str]  # Para weekly: ['monday', 'tuesday', ...]
    enabled: bool = True
    created_at: datetime = None
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class Scheduler:
    """Sistema de agendamento"""
    
    def __init__(self, config):
        self.config = config
        self.running = False
        self.rules = []
        self.callbacks = []
        
        # Configuração
        self.rules_file = Path("schedules.json")
        self.check_interval = 1  # segundos
        
        # Carregar regras salvas
        self._load_rules()
    
    async def initialize(self):
        """Inicializar agendador"""
        try:
            logger.info("⏰ Inicializando sistema de agendamento")
            
            # Configurar regras carregadas
            for rule in self.rules:
                if rule.enabled:
                    self._schedule_rule(rule)
            
            logger.info(f"✅ Sistema de agendamento inicializado com {len(self.rules)} regras")
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar agendador: {e}")
            raise
    
    async def start_scheduler(self):
        """Iniciar agendador"""
        try:
            logger.info("⏰ Iniciando agendador")
            self.running = True
            
            while self.running:
                try:
                    # Executar tarefas agendadas
                    schedule.run_pending()
                    
                    # Atualizar próximas execuções
                    self._update_next_runs()
                    
                    # Aguardar próximo ciclo
                    await asyncio.sleep(self.check_interval)
                    
                except Exception as e:
                    logger.error(f"❌ Erro no agendador: {e}")
                    await asyncio.sleep(5)  # Aguardar antes de tentar novamente
                    
        except Exception as e:
            logger.error(f"❌ Erro no agendador: {e}")
        finally:
            self.running = False
            logger.info("🛑 Agendador parado")
    
    def _schedule_rule(self, rule: ScheduleRule):
        """Agendar uma regra"""
        try:
            if rule.frequency == ScheduleFrequency.DAILY:
                getattr(schedule.every(), 'day').at(rule.time).do(
                    self._execute_rule, rule
                )
            
            elif rule.frequency == ScheduleFrequency.WEEKLY:
                for day in rule.days:
                    try:
                        getattr(schedule.every(), day.lower()).at(rule.time).do(
                            self._execute_rule, rule
                        )
                    except AttributeError:
                        logger.error(f"❌ Dia inválido: {day}")
            
            elif rule.frequency == ScheduleFrequency.MONTHLY:
                # Para mensal, usar o dia do mês
                day = int(rule.time.split(':')[0])  # Usar hora como dia do mês
                schedule.every().month.do(self._execute_rule, rule)
            
            logger.info(f"✅ Regra agendada: {rule.name} - {rule.frequency.value} às {rule.time}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao agendar regra {rule.name}: {e}")
    
    def _execute_rule(self, rule: ScheduleRule):
        """Executar uma regra agendada"""
        try:
            logger.info(f"⏰ Executando regra: {rule.name}")
            
            # Atualizar estatísticas
            rule.last_run = datetime.now()
            rule.run_count += 1
            
            # Executar ação
            asyncio.create_task(self._execute_action(rule))
            
            # Executar callbacks
            for callback in self.callbacks:
                try:
                    callback(rule)
                except Exception as e:
                    logger.error(f"❌ Erro em callback de agendamento: {e}")
            
            # Salvar regras
            self._save_rules()
            
        except Exception as e:
            logger.error(f"❌ Erro ao executar regra {rule.name}: {e}")
    
    async def _execute_action(self, rule: ScheduleRule):
        """Executar ação da regra"""
        try:
            action = rule.action
            parameters = rule.parameters
            
            if action == ScheduleAction.SLEEP_ASICS:
                await self._sleep_asics(parameters)
            
            elif action == ScheduleAction.RESUME_ASICS:
                await self._resume_asics(parameters)
            
            elif action == ScheduleAction.ADJUST_FAN_SPEED:
                await self._adjust_fan_speed(parameters)
            
            elif action == ScheduleAction.START_EXHAUST:
                await self._start_exhaust(parameters)
            
            elif action == ScheduleAction.STOP_EXHAUST:
                await self._stop_exhaust(parameters)
            
            elif action == ScheduleAction.SEND_ALERT:
                await self._send_alert(parameters)
            
            elif action == ScheduleAction.CUSTOM_COMMAND:
                await self._execute_custom_command(parameters)
            
            logger.info(f"✅ Ação executada: {action.value}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao executar ação {rule.action.value}: {e}")
    
    async def _sleep_asics(self, parameters: Dict[str, Any]):
        """Colocar ASICs em sleep"""
        try:
            logger.info("😴 Colocando ASICs em sleep (agendado)")
            # Em produção, integrar com gerenciador de ASICs
            # await self.asic_manager.sleep_all()
            
        except Exception as e:
            logger.error(f"❌ Erro ao colocar ASICs em sleep: {e}")
    
    async def _resume_asics(self, parameters: Dict[str, Any]):
        """Retomar ASICs"""
        try:
            logger.info("▶️ Retomando ASICs (agendado)")
            # Em produção, integrar com gerenciador de ASICs
            # await self.asic_manager.resume_all()
            
        except Exception as e:
            logger.error(f"❌ Erro ao retomar ASICs: {e}")
    
    async def _adjust_fan_speed(self, parameters: Dict[str, Any]):
        """Ajustar velocidade do ventilador"""
        try:
            fan_speed = parameters.get('fan_speed', 50)
            logger.info(f"🌀 Ajustando ventilador para {fan_speed}% (agendado)")
            # Em produção, integrar com controle de ventiladores
            # await self.fan_controller.set_speed(fan_speed)
            
        except Exception as e:
            logger.error(f"❌ Erro ao ajustar velocidade do ventilador: {e}")
    
    async def _start_exhaust(self, parameters: Dict[str, Any]):
        """Iniciar exaustor"""
        try:
            logger.info("🌀 Iniciando exaustor (agendado)")
            # Em produção, integrar com controle de exaustor
            # await self.exhaust_controller.start()
            
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar exaustor: {e}")
    
    async def _stop_exhaust(self, parameters: Dict[str, Any]):
        """Parar exaustor"""
        try:
            logger.info("🌀 Parando exaustor (agendado)")
            # Em produção, integrar com controle de exaustor
            # await self.exhaust_controller.stop()
            
        except Exception as e:
            logger.error(f"❌ Erro ao parar exaustor: {e}")
    
    async def _send_alert(self, parameters: Dict[str, Any]):
        """Enviar alerta"""
        try:
            message = parameters.get('message', 'Alerta agendado')
            logger.info(f"🚨 Enviando alerta: {message}")
            # Em produção, integrar com sistema de notificações
            # await self.notification_manager.send_alert("scheduled", message, "info")
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar alerta: {e}")
    
    async def _execute_custom_command(self, parameters: Dict[str, Any]):
        """Executar comando customizado"""
        try:
            command = parameters.get('command', '')
            logger.info(f"⚙️ Executando comando customizado: {command}")
            # Em produção, implementar execução de comandos customizados
            
        except Exception as e:
            logger.error(f"❌ Erro ao executar comando customizado: {e}")
    
    def add_rule(self, rule: ScheduleRule) -> bool:
        """Adicionar nova regra"""
        try:
            # Verificar se ID já existe
            if any(r.id == rule.id for r in self.rules):
                logger.error(f"❌ Regra com ID {rule.id} já existe")
                return False
            
            # Adicionar regra
            self.rules.append(rule)
            
            # Agendar se estiver habilitada
            if rule.enabled:
                self._schedule_rule(rule)
            
            # Salvar regras
            self._save_rules()
            
            logger.info(f"✅ Regra adicionada: {rule.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao adicionar regra: {e}")
            return False
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remover regra"""
        try:
            # Encontrar regra
            rule = next((r for r in self.rules if r.id == rule_id), None)
            if not rule:
                logger.error(f"❌ Regra {rule_id} não encontrada")
                return False
            
            # Remover da lista
            self.rules.remove(rule)
            
            # Limpar agendamento (schedule não tem método para remover, então recriar)
            schedule.clear()
            for r in self.rules:
                if r.enabled:
                    self._schedule_rule(r)
            
            # Salvar regras
            self._save_rules()
            
            logger.info(f"✅ Regra removida: {rule.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao remover regra: {e}")
            return False
    
    def update_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """Atualizar regra"""
        try:
            # Encontrar regra
            rule = next((r for r in self.rules if r.id == rule_id), None)
            if not rule:
                logger.error(f"❌ Regra {rule_id} não encontrada")
                return False
            
            # Atualizar campos
            for key, value in updates.items():
                if hasattr(rule, key):
                    setattr(rule, key, value)
            
            # Recriar agendamento
            schedule.clear()
            for r in self.rules:
                if r.enabled:
                    self._schedule_rule(r)
            
            # Salvar regras
            self._save_rules()
            
            logger.info(f"✅ Regra atualizada: {rule.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar regra: {e}")
            return False
    
    def enable_rule(self, rule_id: str) -> bool:
        """Habilitar regra"""
        return self.update_rule(rule_id, {'enabled': True})
    
    def disable_rule(self, rule_id: str) -> bool:
        """Desabilitar regra"""
        return self.update_rule(rule_id, {'enabled': False})
    
    def get_rule(self, rule_id: str) -> Optional[ScheduleRule]:
        """Obter regra por ID"""
        return next((r for r in self.rules if r.id == rule_id), None)
    
    def get_all_rules(self) -> List[ScheduleRule]:
        """Obter todas as regras"""
        return self.rules.copy()
    
    def get_active_rules(self) -> List[ScheduleRule]:
        """Obter regras ativas"""
        return [r for r in self.rules if r.enabled]
    
    def _update_next_runs(self):
        """Atualizar próximas execuções"""
        try:
            for rule in self.rules:
                if rule.enabled:
                    # Calcular próxima execução baseada na frequência
                    next_run = self._calculate_next_run(rule)
                    rule.next_run = next_run
                    
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar próximas execuções: {e}")
    
    def _calculate_next_run(self, rule: ScheduleRule) -> Optional[datetime]:
        """Calcular próxima execução"""
        try:
            now = datetime.now()
            
            if rule.frequency == ScheduleFrequency.DAILY:
                # Próxima execução hoje ou amanhã
                today_time = datetime.strptime(rule.time, "%H:%M").time()
                today_run = datetime.combine(now.date(), today_time)
                
                if today_run > now:
                    return today_run
                else:
                    return today_run + timedelta(days=1)
            
            elif rule.frequency == ScheduleFrequency.WEEKLY:
                # Próxima execução na próxima semana
                # Implementação simplificada - retornar em 7 dias
                return now + timedelta(days=7)
            
            elif rule.frequency == ScheduleFrequency.MONTHLY:
                # Próxima execução no próximo mês
                return now + timedelta(days=30)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao calcular próxima execução: {e}")
            return None
    
    def _load_rules(self):
        """Carregar regras do arquivo"""
        try:
            if not self.rules_file.exists():
                self._save_rules()
                return
            
            with open(self.rules_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.rules = []
            for rule_data in data.get('rules', []):
                # Converter string de data para datetime
                if rule_data.get('created_at'):
                    rule_data['created_at'] = datetime.fromisoformat(rule_data['created_at'])
                if rule_data.get('last_run'):
                    rule_data['last_run'] = datetime.fromisoformat(rule_data['last_run'])
                if rule_data.get('next_run'):
                    rule_data['next_run'] = datetime.fromisoformat(rule_data['next_run'])
                
                rule = ScheduleRule(**rule_data)
                self.rules.append(rule)
            
            logger.info(f"✅ {len(self.rules)} regras carregadas")
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar regras: {e}")
            self.rules = []
    
    def _save_rules(self):
        """Salvar regras no arquivo"""
        try:
            data = {
                'rules': []
            }
            
            for rule in self.rules:
                rule_data = asdict(rule)
                
                # Converter datetime para string
                if rule_data.get('created_at'):
                    rule_data['created_at'] = rule_data['created_at'].isoformat()
                if rule_data.get('last_run'):
                    rule_data['last_run'] = rule_data['last_run'].isoformat()
                if rule_data.get('next_run'):
                    rule_data['next_run'] = rule_data['next_run'].isoformat()
                
                data['rules'].append(rule_data)
            
            with open(self.rules_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar regras: {e}")
    
    def add_callback(self, callback: Callable[[ScheduleRule], None]):
        """Adicionar callback para execução de regras"""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[ScheduleRule], None]):
        """Remover callback"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obter estatísticas do agendador"""
        try:
            active_rules = len([r for r in self.rules if r.enabled])
            total_runs = sum(r.run_count for r in self.rules)
            
            return {
                'total_rules': len(self.rules),
                'active_rules': active_rules,
                'disabled_rules': len(self.rules) - active_rules,
                'total_runs': total_runs,
                'rules_with_runs': len([r for r in self.rules if r.run_count > 0])
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao calcular estatísticas: {e}")
            return {}
    
    def is_active(self) -> bool:
        """Verificar se o agendador está ativo"""
        return self.running
    
    async def stop(self):
        """Parar agendador"""
        try:
            logger.info("🛑 Parando agendador")
            self.running = False
            schedule.clear()
            logger.info("✅ Agendador parado")
                
        except Exception as e:
            logger.error(f"❌ Erro ao parar agendador: {e}")


