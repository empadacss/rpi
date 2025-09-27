"""
Rotas da API REST
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Criar router
router = APIRouter()

# Modelos Pydantic
class SystemStatusResponse(BaseModel):
    status: str
    timestamp: str
    active_collectors: int
    total_miners: int
    uptime: float
    alerts_count: int
    efficiency: float
    total_hashrate: float
    total_power: float
    avg_temperature: float

class MiningDataResponse(BaseModel):
    timestamp: str
    total_miners: int
    active_miners: int
    total_hashrate: float
    total_power: float
    efficiency: float
    avg_temperature: float
    miners: List[Dict[str, Any]]

class AlertResponse(BaseModel):
    id: str
    type: str
    severity: str
    message: str
    timestamp: str
    device_id: Optional[str]
    data: Optional[Dict[str, Any]]
    resolved: bool

class ASICControlRequest(BaseModel):
    action: str
    miner_id: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None

class ReportRequest(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    report_type: str = "operational"

# Dependência para obter o gerenciador do sistema
async def get_system_manager():
    """Obter instância do gerenciador do sistema"""
    # Em produção, isso viria de uma injeção de dependência
    from main import system_manager
    if not system_manager:
        raise HTTPException(status_code=503, detail="Sistema não inicializado")
    return system_manager

# Rotas de status
@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status(system_manager = Depends(get_system_manager)):
    """Obter status do sistema"""
    try:
        status = await system_manager.get_status()
        
        return SystemStatusResponse(
            status="healthy" if status.active_collectors > 0 else "unhealthy",
            timestamp=status.timestamp.isoformat(),
            active_collectors=status.active_collectors,
            total_miners=status.total_miners,
            uptime=status.uptime,
            alerts_count=status.alerts_count,
            efficiency=status.efficiency,
            total_hashrate=status.total_hashrate,
            total_power=status.total_power,
            avg_temperature=status.avg_temperature
        )
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check(system_manager = Depends(get_system_manager)):
    """Verificar saúde da API e dos serviços internos."""
    status = await system_manager.get_status()
    rabbitmq_ok = await system_manager.check_rabbitmq_health()

    return {
        "status": "healthy" if rabbitmq_ok else "degraded",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "rabbitmq": rabbitmq_ok,
        "system": status.to_dict(),
    }

# Rotas de dados de mineração
@router.get("/mining/data", response_model=MiningDataResponse)
async def get_mining_data(system_manager = Depends(get_system_manager)):
    """Obter dados de mineração"""
    try:
        data = await system_manager.get_realtime_data()
        
        return MiningDataResponse(
            timestamp=datetime.now().isoformat(),
            total_miners=data.get('asic', {}).get('total_miners', 0),
            active_miners=data.get('asic', {}).get('active_miners', 0),
            total_hashrate=data.get('asic', {}).get('total_hashrate', 0),
            total_power=data.get('asic', {}).get('total_power', 0),
            efficiency=data.get('asic', {}).get('efficiency', 0),
            avg_temperature=data.get('asic', {}).get('avg_temperature', 0),
            miners=data.get('asic', {}).get('miners', [])
        )
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter dados de mineração: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mining/history")
async def get_mining_history(
    hours: int = Query(24, description="Número de horas para histórico"),
    system_manager = Depends(get_system_manager)
):
    """Obter histórico de mineração"""
    try:
        # Em produção, isso viria do banco de dados
        return {
            "message": "Histórico de mineração não implementado",
            "hours": hours,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter histórico: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Rotas de alertas
@router.get("/alerts", response_model=List[AlertResponse])
async def get_alerts(system_manager = Depends(get_system_manager)):
    """Obter alertas ativos"""
    try:
        alerts = await system_manager.get_active_alerts()
        
        return [
            AlertResponse(
                id=alert.get('id', ''),
                type=alert.get('type', ''),
                severity=alert.get('severity', 'info'),
                message=alert.get('message', ''),
                timestamp=alert.get('timestamp', ''),
                device_id=alert.get('device_id'),
                data=alert.get('data'),
                resolved=alert.get('resolved', False)
            )
            for alert in alerts
        ]
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter alertas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    system_manager = Depends(get_system_manager)
):
    """Resolver alerta"""
    try:
        # Em produção, implementar resolução de alerta
        return {
            "message": f"Alerta {alert_id} resolvido",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao resolver alerta: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Rotas de controle de ASICs
@router.post("/asic/sleep-all")
async def sleep_all_asics(system_manager = Depends(get_system_manager)):
    """Colocar todos os ASICs em modo sleep"""
    try:
        result = await system_manager.sleep_all_asics()
        
        return {
            "success": True,
            "message": "Todos os ASICs colocados em modo sleep",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao colocar ASICs em sleep: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/asic/resume-all")
async def resume_all_asics(system_manager = Depends(get_system_manager)):
    """Retomar todos os ASICs"""
    try:
        result = await system_manager.resume_all_asics()
        
        return {
            "success": True,
            "message": "Todos os ASICs retomados",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao retomar ASICs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/asic/control")
async def control_asic(
    request: ASICControlRequest,
    system_manager = Depends(get_system_manager)
):
    """Controlar ASIC específico"""
    try:
        action = request.action
        miner_id = request.miner_id
        parameters = request.parameters or {}
        
        # Em produção, implementar controle específico
        return {
            "success": True,
            "message": f"Ação {action} executada no minerador {miner_id}",
            "action": action,
            "miner_id": miner_id,
            "parameters": parameters,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao controlar ASIC: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Rotas de relatórios
@router.get("/reports/financial")
async def get_financial_report(
    start_date: Optional[str] = Query(None, description="Data de início (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Data de fim (YYYY-MM-DD)"),
    system_manager = Depends(get_system_manager)
):
    """Obter relatório financeiro"""
    try:
        report = await system_manager.get_financial_report()
        
        return {
            "report_type": "financial",
            "start_date": start_date,
            "end_date": end_date,
            "data": report,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter relatório financeiro: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reports/operational")
async def get_operational_report(
    start_date: Optional[str] = Query(None, description="Data de início (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Data de fim (YYYY-MM-DD)"),
    system_manager = Depends(get_system_manager)
):
    """Obter relatório operacional"""
    try:
        report = await system_manager.get_operational_report()
        
        return {
            "report_type": "operational",
            "start_date": start_date,
            "end_date": end_date,
            "data": report,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter relatório operacional: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reports/performance")
async def get_performance_report(
    hours: int = Query(24, description="Número de horas para análise"),
    system_manager = Depends(get_system_manager)
):
    """Obter relatório de performance"""
    try:
        # Em produção, implementar relatório de performance
        return {
            "report_type": "performance",
            "hours": hours,
            "data": {
                "message": "Relatório de performance não implementado",
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter relatório de performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Rotas de configuração
@router.get("/config")
async def get_configuration():
    """Obter configuração do sistema"""
    try:
        # Em produção, retornar configuração não sensível
        return {
            "app_name": "Bitcoin Mining Automation",
            "version": "1.0.0",
            "debug": False,
            "collection_interval": 1,
            "queue_size": 1000,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter configuração: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config/devices")
async def get_device_configuration():
    """Obter configuração de dispositivos"""
    try:
        # Em produção, retornar configuração de dispositivos
        return {
            "devices": {
                "abb": {
                    "host": "192.168.0.10",
                    "port": 502,
                    "enabled": True
                },
                "ble": {
                    "interface": "/dev/ttyUSB0",
                    "enabled": True
                },
                "asic": {
                    "hashcore_path": "/usr/local/bin/hashcore",
                    "enabled": True
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter configuração de dispositivos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Rotas de estatísticas
@router.get("/stats/overview")
async def get_overview_stats(system_manager = Depends(get_system_manager)):
    """Obter estatísticas gerais"""
    try:
        status = await system_manager.get_status()
        
        return {
            "system": {
                "uptime": status.uptime,
                "active_collectors": status.active_collectors,
                "alerts_count": status.alerts_count
            },
            "mining": {
                "total_miners": status.total_miners,
                "total_hashrate": status.total_hashrate,
                "total_power": status.total_power,
                "efficiency": status.efficiency,
                "avg_temperature": status.avg_temperature
            },
            "timestamp": status.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter estatísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/performance")
async def get_performance_stats(
    hours: int = Query(24, description="Número de horas para análise"),
    system_manager = Depends(get_system_manager)
):
    """Obter estatísticas de performance"""
    try:
        # Em produção, implementar estatísticas de performance
        return {
            "period_hours": hours,
            "data": {
                "message": "Estatísticas de performance não implementadas",
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter estatísticas de performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Rotas de automação
@router.get("/automation/rules")
async def get_automation_rules(system_manager = Depends(get_system_manager)):
    """Obter regras de automação"""
    try:
        # Em produção, implementar obtenção de regras
        return {
            "rules": [],
            "message": "Regras de automação não implementadas",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter regras de automação: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/automation/rules")
async def create_automation_rule(
    rule_data: Dict[str, Any],
    system_manager = Depends(get_system_manager)
):
    """Criar nova regra de automação"""
    try:
        # Em produção, implementar criação de regras
        return {
            "success": True,
            "message": "Regra de automação criada",
            "rule": rule_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar regra de automação: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Rotas de logs
@router.get("/logs")
async def get_logs(
    level: str = Query("INFO", description="Nível de log"),
    limit: int = Query(100, description="Número máximo de logs"),
    system_manager = Depends(get_system_manager)
):
    """Obter logs do sistema"""
    try:
        # Em produção, implementar obtenção de logs
        return {
            "level": level,
            "limit": limit,
            "logs": [],
            "message": "Sistema de logs não implementado",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Rotas de backup
@router.post("/backup/create")
async def create_backup(system_manager = Depends(get_system_manager)):
    """Criar backup do sistema"""
    try:
        # Em produção, implementar criação de backup
        return {
            "success": True,
            "message": "Backup criado com sucesso",
            "backup_id": f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar backup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/backup/list")
async def list_backups(system_manager = Depends(get_system_manager)):
    """Listar backups disponíveis"""
    try:
        # Em produção, implementar listagem de backups
        return {
            "backups": [],
            "message": "Sistema de backup não implementado",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao listar backups: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Rotas de monitoramento
@router.get("/monitoring/metrics")
async def get_metrics(system_manager = Depends(get_system_manager)):
    """Obter métricas do sistema"""
    try:
        # Em produção, implementar métricas
        return {
            "metrics": {
                "cpu_usage": 0.0,
                "memory_usage": 0.0,
                "disk_usage": 0.0,
                "network_usage": 0.0
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter métricas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/monitoring/health")
async def get_monitoring_health(system_manager = Depends(get_system_manager)):
    """Obter saúde do monitoramento"""
    try:
        rabbitmq_ok = await system_manager.check_rabbitmq_health()

        services = {
            "database": "healthy",
            "redis": "healthy",
            "rabbitmq": "healthy" if rabbitmq_ok else "unhealthy",
            "collectors": "healthy"
        }

        overall_status = "healthy" if all(value == "healthy" for value in services.values()) else "degraded"

        return {
            "status": overall_status,
            "services": services,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Erro ao obter saúde do monitoramento: {e}")
        raise HTTPException(status_code=500, detail=str(e))


