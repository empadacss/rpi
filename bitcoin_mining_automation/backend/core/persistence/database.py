"""
Sistema de persistência de dados
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID
import uuid

logger = logging.getLogger(__name__)

Base = declarative_base()

class ABBReading(Base):
    """Leitura do inversor ABB"""
    __tablename__ = "abb_readings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    device_id = Column(String(100), nullable=False)
    voltage = Column(Float)
    current = Column(Float)
    power = Column(Float)
    frequency = Column(Float)
    energy = Column(Float)
    connected = Column(Boolean, default=True)
    error_message = Column(Text)
    raw_data = Column(JSON)

class BLEReading(Base):
    """Leitura de sensores BLE"""
    __tablename__ = "ble_readings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    device_id = Column(String(100), nullable=False)
    temperature = Column(Float)
    humidity = Column(Float)
    pressure = Column(Float)
    connected = Column(Boolean, default=True)
    error_message = Column(Text)
    raw_data = Column(JSON)

class ASICReading(Base):
    """Leitura dos ASICs"""
    __tablename__ = "asic_readings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    miner_id = Column(String(100), nullable=False)
    ip_address = Column(String(45))
    model = Column(String(100))
    status = Column(String(50))
    hashrate = Column(Float)
    power = Column(Float)
    temperature = Column(Float)
    fan_speed = Column(Integer)
    uptime = Column(Integer)
    errors = Column(Integer)
    efficiency = Column(Float)
    connected = Column(Boolean, default=True)
    error_message = Column(Text)
    raw_data = Column(JSON)

class PoolReading(Base):
    """Leitura da pool de mineração"""
    __tablename__ = "pool_readings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    pool_name = Column(String(100), nullable=False)
    total_hashrate = Column(Float)
    our_hashrate = Column(Float)
    efficiency = Column(Float)
    active_workers = Column(Integer)
    shares_accepted = Column(Integer)
    shares_rejected = Column(Integer)
    last_share_time = Column(DateTime)
    connected = Column(Boolean, default=True)
    error_message = Column(Text)
    raw_data = Column(JSON)

class Alert(Base):
    """Alertas do sistema"""
    __tablename__ = "alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    alert_type = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    device_id = Column(String(100))
    data = Column(JSON)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    resolved_by = Column(String(100))

class SystemStatus(Base):
    """Status do sistema"""
    __tablename__ = "system_status"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    total_miners = Column(Integer)
    active_miners = Column(Integer)
    total_hashrate = Column(Float)
    total_power = Column(Float)
    avg_temperature = Column(Float)
    efficiency = Column(Float)
    uptime = Column(Float)
    alerts_count = Column(Integer)
    status_data = Column(JSON)

class DatabaseManager:
    """Gerenciador de banco de dados"""
    
    def __init__(self, config):
        self.config = config
        self.engine = None
        self.SessionLocal = None
        self.running = False
        
    async def initialize(self):
        """Inicializar banco de dados"""
        try:
            logger.info("🗄️ Inicializando banco de dados")
            
            # Criar engine
            self.engine = create_engine(
                self.config.database_url,
                echo=self.config.debug,
                pool_pre_ping=True,
                pool_recycle=300
            )
            
            # Criar session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Criar tabelas
            Base.metadata.create_all(bind=self.engine)
            
            logger.info("✅ Banco de dados inicializado com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar banco de dados: {e}")
            raise
    
    def get_session(self) -> Session:
        """Obter sessão do banco de dados"""
        return self.SessionLocal()
    
    async def save_abb_reading(self, data: Dict[str, Any]) -> bool:
        """Salvar leitura do ABB"""
        try:
            with self.get_session() as session:
                reading = ABBReading(
                    device_id=data.get('device_id', 'unknown'),
                    voltage=data.get('data', {}).get('voltage'),
                    current=data.get('data', {}).get('current'),
                    power=data.get('data', {}).get('power'),
                    frequency=data.get('data', {}).get('frequency'),
                    energy=data.get('data', {}).get('energy'),
                    connected=data.get('data', {}).get('connected', True),
                    error_message=data.get('data', {}).get('error'),
                    raw_data=data
                )
                
                session.add(reading)
                session.commit()
                
                logger.debug(f"✅ Leitura ABB salva: {data.get('device_id')}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Erro ao salvar leitura ABB: {e}")
            return False
    
    async def save_ble_reading(self, data: Dict[str, Any]) -> bool:
        """Salvar leitura BLE"""
        try:
            with self.get_session() as session:
                reading = BLEReading(
                    device_id=data.get('device_id', 'unknown'),
                    temperature=data.get('data', {}).get('temperature'),
                    humidity=data.get('data', {}).get('humidity'),
                    pressure=data.get('data', {}).get('pressure'),
                    connected=data.get('data', {}).get('connected', True),
                    error_message=data.get('data', {}).get('error'),
                    raw_data=data
                )
                
                session.add(reading)
                session.commit()
                
                logger.debug(f"✅ Leitura BLE salva: {data.get('device_id')}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Erro ao salvar leitura BLE: {e}")
            return False
    
    async def save_asic_reading(self, data: Dict[str, Any]) -> bool:
        """Salvar leitura dos ASICs"""
        try:
            with self.get_session() as session:
                # Salvar dados gerais
                if 'total_hashrate' in data:
                    system_status = SystemStatus(
                        total_miners=data.get('total_miners', 0),
                        active_miners=data.get('active_miners', 0),
                        total_hashrate=data.get('total_hashrate', 0),
                        total_power=data.get('total_power', 0),
                        avg_temperature=data.get('avg_temperature', 0),
                        efficiency=data.get('efficiency', 0),
                        status_data=data
                    )
                    session.add(system_status)
                
                # Salvar dados de cada minerador
                for miner_data in data.get('miners', []):
                    reading = ASICReading(
                        miner_id=miner_data.get('id', 'unknown'),
                        ip_address=miner_data.get('ip', ''),
                        model=miner_data.get('model', ''),
                        status=miner_data.get('status', 'unknown'),
                        hashrate=miner_data.get('hashrate', 0),
                        power=miner_data.get('power', 0),
                        temperature=miner_data.get('temperature', 0),
                        fan_speed=miner_data.get('fan_speed', 0),
                        uptime=miner_data.get('uptime', 0),
                        errors=miner_data.get('errors', 0),
                        efficiency=miner_data.get('efficiency', 0),
                        connected=miner_data.get('connected', True),
                        error_message=miner_data.get('error_message'),
                        raw_data=miner_data
                    )
                    session.add(reading)
                
                session.commit()
                
                logger.debug(f"✅ Leitura ASIC salva: {len(data.get('miners', []))} mineradores")
                return True
                
        except Exception as e:
            logger.error(f"❌ Erro ao salvar leitura ASIC: {e}")
            return False
    
    async def save_pool_reading(self, data: Dict[str, Any]) -> bool:
        """Salvar leitura da pool"""
        try:
            with self.get_session() as session:
                reading = PoolReading(
                    pool_name=data.get('pool_name', 'unknown'),
                    total_hashrate=data.get('total_hashrate', 0),
                    our_hashrate=data.get('our_hashrate', 0),
                    efficiency=data.get('efficiency', 0),
                    active_workers=data.get('active_workers', 0),
                    shares_accepted=data.get('shares_accepted', 0),
                    shares_rejected=data.get('shares_rejected', 0),
                    last_share_time=data.get('last_share_time'),
                    connected=data.get('connected', True),
                    error_message=data.get('error_message'),
                    raw_data=data
                )
                
                session.add(reading)
                session.commit()
                
                logger.debug(f"✅ Leitura Pool salva: {data.get('pool_name')}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Erro ao salvar leitura Pool: {e}")
            return False
    
    async def save_alert(self, alert_type: str, severity: str, message: str, 
                        device_id: Optional[str] = None, data: Optional[Dict[str, Any]] = None) -> bool:
        """Salvar alerta"""
        try:
            with self.get_session() as session:
                alert = Alert(
                    alert_type=alert_type,
                    severity=severity,
                    message=message,
                    device_id=device_id,
                    data=data
                )
                
                session.add(alert)
                session.commit()
                
                logger.debug(f"✅ Alerta salvo: {alert_type}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Erro ao salvar alerta: {e}")
            return False
    
    async def get_latest_readings(self, device_type: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Obter leituras mais recentes"""
        try:
            with self.get_session() as session:
                if device_type == 'abb':
                    readings = session.query(ABBReading).order_by(ABBReading.timestamp.desc()).limit(limit).all()
                elif device_type == 'ble':
                    readings = session.query(BLEReading).order_by(BLEReading.timestamp.desc()).limit(limit).all()
                elif device_type == 'asic':
                    readings = session.query(ASICReading).order_by(ASICReading.timestamp.desc()).limit(limit).all()
                elif device_type == 'pool':
                    readings = session.query(PoolReading).order_by(PoolReading.timestamp.desc()).limit(limit).all()
                else:
                    return []
                
                return [
                    {
                        'id': str(reading.id),
                        'timestamp': reading.timestamp.isoformat(),
                        'device_id': reading.device_id,
                        'data': reading.raw_data
                    }
                    for reading in readings
                ]
                
        except Exception as e:
            logger.error(f"❌ Erro ao obter leituras: {e}")
            return []
    
    async def get_system_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Obter estatísticas do sistema"""
        try:
            with self.get_session() as session:
                from datetime import timedelta
                cutoff_time = datetime.utcnow() - timedelta(hours=hours)
                
                # Estatísticas gerais
                total_readings = session.query(SystemStatus).filter(
                    SystemStatus.timestamp >= cutoff_time
                ).count()
                
                if total_readings == 0:
                    return {}
                
                # Última leitura
                last_reading = session.query(SystemStatus).order_by(
                    SystemStatus.timestamp.desc()
                ).first()
                
                if not last_reading:
                    return {}
                
                return {
                    'total_readings': total_readings,
                    'last_update': last_reading.timestamp.isoformat(),
                    'total_miners': last_reading.total_miners,
                    'active_miners': last_reading.active_miners,
                    'total_hashrate': last_reading.total_hashrate,
                    'total_power': last_reading.total_power,
                    'avg_temperature': last_reading.avg_temperature,
                    'efficiency': last_reading.efficiency
                }
                
        except Exception as e:
            logger.error(f"❌ Erro ao obter estatísticas: {e}")
            return {}
    
    async def cleanup_old_data(self, days: int = 30):
        """Limpar dados antigos"""
        try:
            with self.get_session() as session:
                from datetime import timedelta
                cutoff_time = datetime.utcnow() - timedelta(days=days)
                
                # Limpar leituras antigas
                abb_count = session.query(ABBReading).filter(
                    ABBReading.timestamp < cutoff_time
                ).delete()
                
                ble_count = session.query(BLEReading).filter(
                    BLEReading.timestamp < cutoff_time
                ).delete()
                
                asic_count = session.query(ASICReading).filter(
                    ASICReading.timestamp < cutoff_time
                ).delete()
                
                pool_count = session.query(PoolReading).filter(
                    PoolReading.timestamp < cutoff_time
                ).delete()
                
                # Limpar status antigo
                status_count = session.query(SystemStatus).filter(
                    SystemStatus.timestamp < cutoff_time
                ).delete()
                
                session.commit()
                
                logger.info(f"✅ Dados antigos removidos: ABB={abb_count}, BLE={ble_count}, ASIC={asic_count}, Pool={pool_count}, Status={status_count}")
                
        except Exception as e:
            logger.error(f"❌ Erro ao limpar dados antigos: {e}")
    
    async def backup_database(self, backup_path: str) -> bool:
        """Fazer backup do banco de dados"""
        try:
            # Em produção, implementar backup real
            logger.info(f"💾 Backup do banco de dados: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao fazer backup: {e}")
            return False
    
    async def restore_database(self, backup_path: str) -> bool:
        """Restaurar banco de dados"""
        try:
            # Em produção, implementar restauração real
            logger.info(f"🔄 Restauração do banco de dados: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao restaurar banco: {e}")
            return False
    
    async def shutdown(self):
        """Parar gerenciador"""
        try:
            logger.info("🛑 Parando gerenciador de banco de dados")
            
            if self.engine:
                self.engine.dispose()
            
            logger.info("✅ Gerenciador de banco de dados parado")
                
        except Exception as e:
            logger.error(f"❌ Erro ao parar gerenciador: {e}")


