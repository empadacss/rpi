"""
Coletor de dados de pools de mineração (F2Pool)
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class PoolCollector:
    """Coletor de dados de pools de mineração"""
    
    def __init__(self, config):
        self.config = config
        self.running = False
        self.latest_data = {}
        self.data_queue = asyncio.Queue(maxsize=1000)
        self.historical_data = []
        
        # Configuração da pool
        self.pool_config = {
            'f2pool': {
                'api_url': 'https://api.f2pool.com/v2',
                'api_token': config.f2pool_api_token,
                'mining_user_name': config.get('mining_user_name', 'USER'),
                'currency': config.get('currency', 'BTC')
            }
        }
        
        # Configuração de coleta
        self.interval = 60  # segundos
        self.timeout = 10   # segundos
        self.max_retries = 3
        
        # Dados atuais
        self.current_hashrate = 0.0
        self.h24_hashrate = 0.0
        self.active_workers = 0
        self.total_workers = 0
        self.shares_accepted = 0
        self.shares_rejected = 0
        self.last_share_time = None
        
    async def initialize(self):
        """Inicializar coletor"""
        try:
            logger.info("🔌 Inicializando coletor de pools")
            
            # Verificar configuração
            if not self.pool_config['f2pool']['api_token']:
                logger.warning("⚠️ Token F2Pool não configurado")
            
            logger.info("✅ Coletor de pools inicializado com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar coletor de pools: {e}")
            raise
    
    async def start_collection(self):
        """Iniciar coleta de dados"""
        try:
            logger.info("📊 Iniciando coleta de dados de pools")
            self.running = True
            
            while self.running:
                try:
                    # Coletar dados da F2Pool
                    await self._collect_f2pool_data()
                    
                    # Aguardar próximo ciclo
                    await asyncio.sleep(self.interval)
                    
                except Exception as e:
                    logger.error(f"❌ Erro na coleta de pools: {e}")
                    await asyncio.sleep(10)  # Aguardar antes de tentar novamente
                    
        except Exception as e:
            logger.error(f"❌ Erro na coleta de pools: {e}")
        finally:
            self.running = False
            logger.info("🛑 Coleta de pools parada")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def _collect_f2pool_data(self):
        """Coletar dados da F2Pool"""
        try:
            if not self.pool_config['f2pool']['api_token']:
                logger.warning("⚠️ Token F2Pool não configurado - pulando coleta")
                return
            
            config = self.pool_config['f2pool']
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Obter informações de hashrate
                info_data = await self._get_f2pool_info(client, config)
                
                # Obter lista de workers
                workers_data = await self._get_f2pool_workers(client, config)
                
                # Processar dados
                if info_data and workers_data:
                    await self._process_f2pool_data(info_data, workers_data)
                
        except Exception as e:
            logger.error(f"❌ Erro ao coletar dados F2Pool: {e}")
            raise
    
    async def _get_f2pool_info(self, client: httpx.AsyncClient, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Obter informações de hashrate da F2Pool"""
        try:
            url = f"{config['api_url']}/hash_rate/info"
            headers = {
                'Content-Type': 'application/json',
                'F2P-API-SECRET': config['api_token']
            }
            payload = {
                'mining_user_name': config['mining_user_name'],
                'currency': config['currency']
            }
            
            response = await client.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                logger.debug(f"📊 Dados F2Pool info obtidos: {data}")
                return data
            else:
                logger.error(f"❌ Erro F2Pool info: HTTP {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erro ao obter info F2Pool: {e}")
            return None
    
    async def _get_f2pool_workers(self, client: httpx.AsyncClient, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Obter lista de workers da F2Pool"""
        try:
            url = f"{config['api_url']}/hash_rate/worker/list"
            headers = {
                'Content-Type': 'application/json',
                'F2P-API-SECRET': config['api_token']
            }
            payload = {
                'mining_user_name': config['mining_user_name'],
                'currency': config['currency']
            }
            
            response = await client.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                logger.debug(f"📊 Dados F2Pool workers obtidos: {data}")
                return data
            else:
                logger.error(f"❌ Erro F2Pool workers: HTTP {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erro ao obter workers F2Pool: {e}")
            return None
    
    async def _process_f2pool_data(self, info_data: Dict[str, Any], workers_data: Dict[str, Any]):
        """Processar dados da F2Pool"""
        try:
            # Processar informações de hashrate
            info = info_data.get('info', {})
            current_hashrate = info.get('hash_rate', 0)
            h24_hashrate = info.get('h24_hash_rate', 0)
            
            # Converter para TH/s
            current_th_s = current_hashrate / 1e12 if current_hashrate else 0
            h24_th_s = h24_hashrate / 1e12 if h24_hashrate else 0
            
            # Processar workers
            workers = workers_data.get('workers', [])
            active_workers = sum(1 for w in workers if w.get('status') == 0)
            total_workers = len(workers)
            
            # Calcular shares
            shares_accepted = sum(w.get('shares_1d', 0) for w in workers)
            shares_rejected = sum(w.get('rejects_1d', 0) for w in workers)
            
            # Último share
            last_share_times = [w.get('last_share_time') for w in workers if w.get('last_share_time')]
            last_share_time = max(last_share_times) if last_share_times else None
            
            # Atualizar dados atuais
            self.current_hashrate = current_th_s
            self.h24_hashrate = h24_th_s
            self.active_workers = active_workers
            self.total_workers = total_workers
            self.shares_accepted = shares_accepted
            self.shares_rejected = shares_rejected
            self.last_share_time = last_share_time
            
            # Criar dados formatados
            data = {
                'timestamp': datetime.now(),
                'pool_name': 'f2pool',
                'currency': self.pool_config['f2pool']['currency'],
                'current_hashrate_th_s': current_th_s,
                'h24_hashrate_th_s': h24_th_s,
                'active_workers': active_workers,
                'total_workers': total_workers,
                'shares_accepted': shares_accepted,
                'shares_rejected': shares_rejected,
                'last_share_time': last_share_time,
                'efficiency': self._calculate_efficiency(shares_accepted, shares_rejected),
                'raw_info': info_data,
                'raw_workers': workers_data
            }
            
            # Armazenar dados
            self.latest_data = data
            self.historical_data.append(data)
            
            # Manter apenas os últimos 1000 registros
            if len(self.historical_data) > 1000:
                self.historical_data = self.historical_data[-1000:]
            
            # Adicionar à fila
            await self.data_queue.put(data)
            
            logger.info(f"📊 F2Pool atualizado: {current_th_s:.2f} TH/s, {active_workers}/{total_workers} workers")
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar dados F2Pool: {e}")
    
    def _calculate_efficiency(self, accepted: int, rejected: int) -> float:
        """Calcular eficiência baseada em shares"""
        try:
            total = accepted + rejected
            if total == 0:
                return 0.0
            return accepted / total
        except Exception:
            return 0.0
    
    async def get_latest_data(self) -> Dict[str, Any]:
        """Obter dados mais recentes"""
        return self.latest_data
    
    async def get_data_from_queue(self) -> Optional[Dict[str, Any]]:
        """Obter dados da fila"""
        try:
            return await asyncio.wait_for(self.data_queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            return None
    
    def get_historical_data(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Obter dados históricos"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            return [
                data for data in self.historical_data
                if data['timestamp'] > cutoff_time
            ]
        except Exception as e:
            logger.error(f"❌ Erro ao obter dados históricos: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obter estatísticas da pool"""
        try:
            if not self.historical_data:
                return {}
            
            # Calcular estatísticas dos últimos dados
            recent_data = self.historical_data[-100:]  # Últimos 100 registros
            
            hashrates = [d['current_hashrate_th_s'] for d in recent_data if d['current_hashrate_th_s'] > 0]
            efficiencies = [d['efficiency'] for d in recent_data if d['efficiency'] > 0]
            
            stats = {
                'current_hashrate': self.current_hashrate,
                'h24_hashrate': self.h24_hashrate,
                'active_workers': self.active_workers,
                'total_workers': self.total_workers,
                'efficiency': self.latest_data.get('efficiency', 0),
                'shares_accepted': self.shares_accepted,
                'shares_rejected': self.shares_rejected,
                'last_share_time': self.last_share_time,
                'avg_hashrate': sum(hashrates) / len(hashrates) if hashrates else 0,
                'max_hashrate': max(hashrates) if hashrates else 0,
                'min_hashrate': min(hashrates) if hashrates else 0,
                'avg_efficiency': sum(efficiencies) / len(efficiencies) if efficiencies else 0,
                'data_points': len(recent_data)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Erro ao calcular estatísticas: {e}")
            return {}
    
    def is_active(self) -> bool:
        """Verificar se o coletor está ativo"""
        return self.running
    
    async def test_connection(self) -> bool:
        """Testar conexão com a pool"""
        try:
            if not self.pool_config['f2pool']['api_token']:
                return False
            
            config = self.pool_config['f2pool']
            
            async with httpx.AsyncClient(timeout=5) as client:
                # Testar com endpoint de info
                url = f"{config['api_url']}/hash_rate/info"
                headers = {
                    'Content-Type': 'application/json',
                    'F2P-API-SECRET': config['api_token']
                }
                payload = {
                    'mining_user_name': config['mining_user_name'],
                    'currency': config['currency']
                }
                
                response = await client.post(url, headers=headers, json=payload)
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"❌ Erro no teste de conexão F2Pool: {e}")
            return False
    
    async def stop(self):
        """Parar coletor"""
        try:
            logger.info("🛑 Parando coletor de pools")
            self.running = False
            logger.info("✅ Coletor de pools parado")
                
        except Exception as e:
            logger.error(f"❌ Erro ao parar coletor de pools: {e}")
    
    def get_device_info(self) -> Dict[str, Any]:
        """Obter informações do dispositivo"""
        return {
            'type': 'pool',
            'pool_name': 'f2pool',
            'currency': self.pool_config['f2pool']['currency'],
            'mining_user': self.pool_config['f2pool']['mining_user_name'],
            'active': self.is_active(),
            'current_hashrate': self.current_hashrate,
            'active_workers': self.active_workers,
            'total_workers': self.total_workers
        }


