"""
Coletor de dados dos ASICs via HashCore Toolkit
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import subprocess
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class ASICCollector:
    """Coletor de dados dos ASICs"""
    
    def __init__(self, config):
        self.config = config
        self.running = False
        self.latest_data = {}
        self.data_queue = asyncio.Queue(maxsize=1000)
        self.miners = {}
        
        # Configuração do HashCore
        self.device_config = config.get_device_config('asic')
        self.hashcore_path = self.device_config.get('hashcore_path', '/usr/local/bin/hashcore')
        self.timeout = self.device_config.get('timeout', 30)
        self.retry_attempts = self.device_config.get('retry_attempts', 3)
        self.discovery_interval = self.device_config.get('discovery_interval', 60)
        
        # Configuração de coleta
        self.interval = config.collection_interval
        
        # Verificar se HashCore está disponível
        self._check_hashcore_availability()
    
    def _check_hashcore_availability(self):
        """Verificar se HashCore está disponível"""
        try:
            hashcore_path = Path(self.hashcore_path)
            if not hashcore_path.exists():
                logger.warning(f"⚠️ HashCore não encontrado em {self.hashcore_path}")
                return False
            
            # Testar execução
            result = subprocess.run(
                [self.hashcore_path, '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                logger.info(f"✅ HashCore encontrado: {result.stdout.strip()}")
                return True
            else:
                logger.warning(f"⚠️ HashCore retornou erro: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao verificar HashCore: {e}")
            return False
    
    async def initialize(self):
        """Inicializar coletor"""
        try:
            logger.info("🔌 Inicializando coletor ASIC")
            
            # Descobrir mineradores
            await self._discover_miners()
            
            logger.info("✅ Coletor ASIC inicializado com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar coletor ASIC: {e}")
            raise
    
    async def start_collection(self):
        """Iniciar coleta de dados"""
        try:
            logger.info("📊 Iniciando coleta de dados ASIC")
            self.running = True
            
            # Iniciar descoberta periódica
            discovery_task = asyncio.create_task(self._periodic_discovery())
            
            while self.running:
                try:
                    # Coletar dados de todos os mineradores
                    data = await self._collect_all_miners_data()
                    
                    if data:
                        # Armazenar dados mais recentes
                        self.latest_data = data
                        
                        # Adicionar à fila
                        await self.data_queue.put(data)
                        
                        logger.debug(f"📊 Dados ASIC coletados: {len(data.get('miners', []))} mineradores")
                    
                    # Aguardar próximo ciclo
                    await asyncio.sleep(self.interval)
                    
                except Exception as e:
                    logger.error(f"❌ Erro na coleta ASIC: {e}")
                    await asyncio.sleep(5)  # Aguardar antes de tentar novamente
            
            # Cancelar tarefa de descoberta
            discovery_task.cancel()
                    
        except Exception as e:
            logger.error(f"❌ Erro na coleta ASIC: {e}")
        finally:
            self.running = False
            logger.info("🛑 Coleta ASIC parada")
    
    async def _periodic_discovery(self):
        """Descoberta periódica de mineradores"""
        while self.running:
            try:
                await asyncio.sleep(self.discovery_interval)
                await self._discover_miners()
            except Exception as e:
                logger.error(f"❌ Erro na descoberta periódica: {e}")
    
    async def _discover_miners(self):
        """Descobrir mineradores na rede"""
        try:
            logger.info("🔍 Descobrindo mineradores...")
            
            # Executar comando de descoberta
            result = await self._run_hashcore_command(['discover'])
            
            if result and 'miners' in result:
                discovered_miners = result['miners']
                
                # Atualizar lista de mineradores
                for miner in discovered_miners:
                    miner_id = miner.get('id', miner.get('ip', 'unknown'))
                    self.miners[miner_id] = {
                        'id': miner_id,
                        'ip': miner.get('ip', ''),
                        'model': miner.get('model', ''),
                        'status': 'discovered',
                        'last_seen': datetime.now()
                    }
                
                logger.info(f"✅ Descobertos {len(discovered_miners)} mineradores")
            else:
                logger.warning("⚠️ Nenhum minerador descoberto")
                
        except Exception as e:
            logger.error(f"❌ Erro na descoberta de mineradores: {e}")
    
    async def _collect_all_miners_data(self) -> Optional[Dict[str, Any]]:
        """Coletar dados de todos os mineradores"""
        try:
            if not self.miners:
                logger.warning("⚠️ Nenhum minerador disponível para coleta")
                return None
            
            # Obter status de todos os mineradores
            result = await self._run_hashcore_command(['status'])
            
            if not result:
                return None
            
            # Processar dados
            data = {
                'timestamp': datetime.now(),
                'device_type': 'asic',
                'total_miners': len(self.miners),
                'miners': []
            }
            
            # Processar cada minerador
            for miner_id, miner_info in self.miners.items():
                miner_data = await self._process_miner_data(miner_id, miner_info, result)
                if miner_data:
                    data['miners'].append(miner_data)
            
            # Calcular totais
            data['total_hashrate'] = sum(m.get('hashrate', 0) for m in data['miners'])
            data['total_power'] = sum(m.get('power', 0) for m in data['miners'])
            data['avg_temperature'] = self._calculate_avg_temperature(data['miners'])
            data['active_miners'] = sum(1 for m in data['miners'] if m.get('status') == 'active')
            
            return data
            
        except Exception as e:
            logger.error(f"❌ Erro ao coletar dados dos mineradores: {e}")
            return None
    
    async def _process_miner_data(self, miner_id: str, miner_info: Dict[str, Any], status_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Processar dados de um minerador específico"""
        try:
            # Encontrar dados do minerador no resultado
            miner_status = None
            if 'miners' in status_result:
                for miner in status_result['miners']:
                    if miner.get('id') == miner_id or miner.get('ip') == miner_info.get('ip'):
                        miner_status = miner
                        break
            
            if not miner_status:
                # Minerador não encontrado no status
                return {
                    'id': miner_id,
                    'ip': miner_info.get('ip', ''),
                    'model': miner_info.get('model', ''),
                    'status': 'offline',
                    'error': 'Not found in status',
                    'last_update': datetime.now()
                }
            
            # Processar dados do minerador
            miner_data = {
                'id': miner_id,
                'ip': miner_status.get('ip', miner_info.get('ip', '')),
                'model': miner_status.get('model', miner_info.get('model', '')),
                'status': miner_status.get('status', 'unknown'),
                'hashrate': miner_status.get('hashrate', 0),
                'power': miner_status.get('power', 0),
                'temperature': miner_status.get('temperature', 0),
                'fan_speed': miner_status.get('fan_speed', 0),
                'uptime': miner_status.get('uptime', 0),
                'errors': miner_status.get('errors', 0),
                'efficiency': miner_status.get('efficiency', 0),
                'last_update': datetime.now()
            }
            
            # Atualizar informações do minerador
            self.miners[miner_id].update({
                'status': miner_data['status'],
                'last_seen': datetime.now()
            })
            
            return miner_data
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar dados do minerador {miner_id}: {e}")
            return None
    
    def _calculate_avg_temperature(self, miners: List[Dict[str, Any]]) -> float:
        """Calcular temperatura média dos mineradores"""
        try:
            temperatures = [m.get('temperature', 0) for m in miners if m.get('temperature', 0) > 0]
            if temperatures:
                return sum(temperatures) / len(temperatures)
            return 0.0
        except Exception:
            return 0.0
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def _run_hashcore_command(self, command: List[str]) -> Optional[Dict[str, Any]]:
        """Executar comando HashCore"""
        try:
            full_command = [self.hashcore_path] + command
            
            process = await asyncio.create_subprocess_exec(
                *full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout
            )
            
            if process.returncode != 0:
                logger.error(f"❌ HashCore command failed: {stderr.decode()}")
                return None
            
            # Parse JSON output
            try:
                result = json.loads(stdout.decode())
                return result
            except json.JSONDecodeError as e:
                logger.error(f"❌ Erro ao parsear JSON do HashCore: {e}")
                return None
                
        except asyncio.TimeoutError:
            logger.error(f"❌ Timeout ao executar comando HashCore: {command}")
            return None
        except Exception as e:
            logger.error(f"❌ Erro ao executar comando HashCore: {e}")
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
        return self.running and len(self.miners) > 0
    
    async def get_miner_status(self, miner_id: str) -> Optional[Dict[str, Any]]:
        """Obter status de um minerador específico"""
        try:
            if miner_id not in self.miners:
                return None
            
            # Executar comando de status para minerador específico
            result = await self._run_hashcore_command(['status', '--miner', miner_id])
            
            if result and 'miners' in result and result['miners']:
                return result['miners'][0]
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter status do minerador {miner_id}: {e}")
            return None
    
    async def control_miner(self, miner_id: str, action: str) -> bool:
        """Controlar minerador (sleep, resume, restart)"""
        try:
            if miner_id not in self.miners:
                logger.error(f"❌ Minerador {miner_id} não encontrado")
                return False
            
            # Executar comando de controle
            result = await self._run_hashcore_command([action, '--miner', miner_id])
            
            if result and result.get('success', False):
                logger.info(f"✅ Comando {action} executado no minerador {miner_id}")
                return True
            else:
                logger.error(f"❌ Falha ao executar comando {action} no minerador {miner_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao controlar minerador {miner_id}: {e}")
            return False
    
    async def stop(self):
        """Parar coletor"""
        try:
            logger.info("🛑 Parando coletor ASIC")
            self.running = False
            logger.info("✅ Coletor ASIC parado")
                
        except Exception as e:
            logger.error(f"❌ Erro ao parar coletor ASIC: {e}")
    
    def get_device_info(self) -> Dict[str, Any]:
        """Obter informações do dispositivo"""
        return {
            'type': 'asic',
            'hashcore_path': self.hashcore_path,
            'total_miners': len(self.miners),
            'miners': list(self.miners.keys()),
            'active': self.is_active()
        }


