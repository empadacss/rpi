"""
Coletor de dados do inversor ABB via Modbus
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pymodbus.client.asynchronous import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class ABBCollector:
    """Coletor de dados do inversor ABB"""
    
    def __init__(self, config):
        self.config = config
        self.client = None
        self.running = False
        self.latest_data = {}
        self.data_queue = asyncio.Queue(maxsize=1000)
        
        # Configuração do dispositivo
        self.device_config = config.get_device_config('abb')
        self.host = self.device_config.get('host', '192.168.0.10')
        self.port = self.device_config.get('port', 502)
        self.slave_id = self.device_config.get('slave_id', 1)
        self.registers = self.device_config.get('registers', {})
        
        # Configuração de coleta
        self.interval = config.collection_interval
        self.timeout = config.connection_timeout
        
    async def initialize(self):
        """Inicializar coletor"""
        try:
            logger.info(f"🔌 Inicializando coletor ABB em {self.host}:{self.port}")
            
            # Criar cliente Modbus
            self.client = AsyncModbusTcpClient(
                host=self.host,
                port=self.port,
                timeout=self.timeout
            )
            
            # Conectar
            await self._connect()
            
            logger.info("✅ Coletor ABB inicializado com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar coletor ABB: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def _connect(self):
        """Conectar ao dispositivo"""
        try:
            if not self.client.connected:
                await self.client.connect()
                logger.info(f"✅ Conectado ao ABB em {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"❌ Erro ao conectar ao ABB: {e}")
            raise
    
    async def start_collection(self):
        """Iniciar coleta de dados"""
        try:
            logger.info("📊 Iniciando coleta de dados ABB")
            self.running = True
            
            while self.running:
                try:
                    # Coletar dados
                    data = await self._collect_data()
                    
                    if data:
                        # Armazenar dados mais recentes
                        self.latest_data = data
                        
                        # Adicionar à fila
                        await self.data_queue.put(data)
                        
                        logger.debug(f"📊 Dados ABB coletados: {data}")
                    
                    # Aguardar próximo ciclo
                    await asyncio.sleep(self.interval)
                    
                except Exception as e:
                    logger.error(f"❌ Erro na coleta ABB: {e}")
                    await asyncio.sleep(5)  # Aguardar antes de tentar novamente
                    
        except Exception as e:
            logger.error(f"❌ Erro na coleta ABB: {e}")
        finally:
            self.running = False
            logger.info("🛑 Coleta ABB parada")
    
    async def _collect_data(self) -> Optional[Dict[str, Any]]:
        """Coletar dados do dispositivo"""
        try:
            # Verificar conexão
            if not self.client.connected:
                await self._connect()
            
            # Ler registros
            data = {
                'timestamp': datetime.now(),
                'device_type': 'abb',
                'device_id': f"{self.host}:{self.port}",
                'data': {}
            }
            
            # Ler tensão
            if 'voltage' in self.registers:
                voltage = await self._read_register(
                    self.registers['voltage'],
                    'voltage'
                )
                if voltage is not None:
                    data['data']['voltage'] = voltage
            
            # Ler corrente
            if 'current' in self.registers:
                current = await self._read_register(
                    self.registers['current'],
                    'current'
                )
                if current is not None:
                    data['data']['current'] = current
            
            # Ler potência
            if 'power' in self.registers:
                power = await self._read_register(
                    self.registers['power'],
                    'power'
                )
                if current is not None:
                    data['data']['power'] = power
            
            # Ler frequência
            if 'frequency' in self.registers:
                frequency = await self._read_register(
                    self.registers['frequency'],
                    'frequency'
                )
                if frequency is not None:
                    data['data']['frequency'] = frequency
            
            # Ler energia
            if 'energy' in self.registers:
                energy = await self._read_register(
                    self.registers['energy'],
                    'energy'
                )
                if energy is not None:
                    data['data']['energy'] = energy
            
            # Calcular potência se não disponível
            if 'power' not in data['data'] and 'voltage' in data['data'] and 'current' in data['data']:
                data['data']['power'] = data['data']['voltage'] * data['data']['current']
            
            # Adicionar status de conexão
            data['data']['connected'] = True
            data['data']['last_update'] = datetime.now()
            
            return data
            
        except Exception as e:
            logger.error(f"❌ Erro ao coletar dados ABB: {e}")
            
            # Retornar dados de erro
            return {
                'timestamp': datetime.now(),
                'device_type': 'abb',
                'device_id': f"{self.host}:{self.port}",
                'data': {
                    'connected': False,
                    'error': str(e),
                    'last_update': datetime.now()
                }
            }
    
    async def _read_register(self, address: int, name: str) -> Optional[float]:
        """Ler registro Modbus"""
        try:
            result = await self.client.read_holding_registers(
                address=address,
                count=1,
                unit=self.slave_id
            )
            
            if result.isError():
                logger.warning(f"⚠️ Erro ao ler registro {name} (addr: {address}): {result}")
                return None
            
            # Converter valor (assumindo que está em formato de ponto fixo)
            value = result.registers[0]
            
            # Aplicar escala se necessário (exemplo: dividir por 100)
            if name in ['voltage', 'current', 'power', 'frequency']:
                value = value / 100.0
            
            return float(value)
            
        except Exception as e:
            logger.error(f"❌ Erro ao ler registro {name}: {e}")
            return None
    
    async def get_latest_data(self) -> Dict[str, Any]:
        """Obter dados mais recentes"""
        return self.latest_data
    
    async def get_data_from_queue(self) -> Optional[Dict[str, Any]]:
        """Obter dados da fila"""
        try:
            return await asyncio.wait_for(self.data_queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            return None
    
    def is_active(self) -> bool:
        """Verificar se o coletor está ativo"""
        return self.running and self.client and self.client.connected
    
    async def stop(self):
        """Parar coletor"""
        try:
            logger.info("🛑 Parando coletor ABB")
            self.running = False
            
            if self.client and self.client.connected:
                await self.client.close()
                logger.info("✅ Conexão ABB fechada")
                
        except Exception as e:
            logger.error(f"❌ Erro ao parar coletor ABB: {e}")
    
    async def test_connection(self) -> bool:
        """Testar conexão com o dispositivo"""
        try:
            if not self.client.connected:
                await self._connect()
            
            # Tentar ler um registro
            result = await self.client.read_holding_registers(
                address=0,
                count=1,
                unit=self.slave_id
            )
            
            return not result.isError()
            
        except Exception as e:
            logger.error(f"❌ Erro no teste de conexão ABB: {e}")
            return False
    
    def get_device_info(self) -> Dict[str, Any]:
        """Obter informações do dispositivo"""
        return {
            'type': 'abb',
            'host': self.host,
            'port': self.port,
            'slave_id': self.slave_id,
            'registers': self.registers,
            'connected': self.client.connected if self.client else False,
            'active': self.is_active()
        }


