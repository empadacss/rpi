"""
Coletor de dados de sensores BLE (Xiaomi)
"""

import asyncio
import logging
import math
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass

try:
    from bleak import BleakScanner
    BLE_SUPPORTED = True
except ImportError:
    BLE_SUPPORTED = False
    logging.warning("Bleak não instalado - suporte BLE desabilitado")

try:
    from atc_mi_interface import general_format, atc_mi_advertising_format
    ATC_MI_SUPPORTED = True
except ImportError:
    ATC_MI_SUPPORTED = False
    logging.warning("atc_mi_interface não instalado - decodificação limitada")

logger = logging.getLogger(__name__)

@dataclass
class BLESensorData:
    """Dados de sensor BLE"""
    mac: str
    temperature: Optional[float]
    humidity: Optional[float]
    battery: Optional[int]
    timestamp: datetime
    rssi: Optional[int] = None

class BLECollector:
    """Coletor de dados de sensores BLE"""
    
    def __init__(self, config):
        self.config = config
        self.running = False
        self.latest_data = {}
        self.data_queue = asyncio.Queue(maxsize=1000)
        self.sensor_data = {}
        self.callbacks = []
        
        # Configuração de sensores conhecidos
        self.known_sensors = {
            "A4:C1:38:30:26:23": {"name": "Sensor 1", "location": "Principal"},
            "A4:C1:38:65:D8:21": {"name": "Sensor 2", "location": "Secundário"}
        }
        
        # Configuração de coleta
        self.scan_interval = 5  # segundos
        self.scan_duration = 2  # segundos
        
        if not BLE_SUPPORTED:
            logger.warning("⚠️ Suporte BLE não disponível - bleak não instalado")
    
    async def initialize(self):
        """Inicializar coletor BLE"""
        try:
            if not BLE_SUPPORTED:
                logger.warning("⚠️ Coletor BLE não pode ser inicializado - bleak não disponível")
                return
            
            logger.info("🔌 Inicializando coletor BLE")
            logger.info("✅ Coletor BLE inicializado com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar coletor BLE: {e}")
            raise
    
    async def start_collection(self):
        """Iniciar coleta de dados BLE"""
        try:
            if not BLE_SUPPORTED:
                logger.warning("⚠️ Coleta BLE não iniciada - bleak não disponível")
                return
            
            logger.info("📊 Iniciando coleta de dados BLE")
            self.running = True
            
            # Iniciar scanner BLE
            scanner_task = asyncio.create_task(self._ble_scan_loop())
            
            # Aguardar até parar
            await scanner_task
            
        except Exception as e:
            logger.error(f"❌ Erro na coleta BLE: {e}")
        finally:
            self.running = False
            logger.info("🛑 Coleta BLE parada")
    
    async def _ble_scan_loop(self):
        """Loop principal de escaneamento BLE"""
        try:
            scanner = BleakScanner(detection_callback=self._detection_callback)
            
            while self.running:
                try:
                    await scanner.start()
                    await asyncio.sleep(self.scan_duration)
                    await scanner.stop()
                    await asyncio.sleep(self.scan_interval)
                except Exception as e:
                    logger.error(f"❌ Erro no scanner BLE: {e}")
                    await asyncio.sleep(5)  # Aguardar antes de tentar novamente
                    
        except Exception as e:
            logger.error(f"❌ Erro no loop de escaneamento BLE: {e}")
    
    def _detection_callback(self, device, advertisement_data):
        """Callback para detecção de dispositivos BLE"""
        try:
            mac = device.address.upper()
            
            # Verificar se é um sensor conhecido
            if mac not in self.known_sensors:
                return
            
            # Extrair dados do anúncio
            frame = None
            if advertisement_data.service_data:
                for uuid, value in advertisement_data.service_data.items():
                    frame = value
                    break
            elif advertisement_data.manufacturer_data:
                for m_id, value in advertisement_data.manufacturer_data.items():
                    frame = value
                    break
            
            if not frame or len(frame) < 11:
                return
            
            # Decodificar dados
            sensor_data = self._decode_advertisement_data(mac, frame, advertisement_data)
            if sensor_data:
                # Armazenar dados
                self.sensor_data[mac] = sensor_data
                self.latest_data[mac] = sensor_data
                
                # Adicionar à fila
                asyncio.create_task(self.data_queue.put(sensor_data))
                
                # Executar callbacks
                for callback in self.callbacks:
                    try:
                        callback(sensor_data)
                    except Exception as e:
                        logger.error(f"❌ Erro em callback BLE: {e}")
                
                logger.debug(f"📊 Dados BLE coletados: {mac} - Temp: {sensor_data.temperature}°C, Hum: {sensor_data.humidity}%")
                
        except Exception as e:
            logger.error(f"❌ Erro no callback de detecção BLE: {e}")
    
    def _decode_advertisement_data(self, mac: str, frame: bytes, advertisement_data) -> Optional[BLESensorData]:
        """Decodificar dados do anúncio BLE"""
        try:
            if ATC_MI_SUPPORTED:
                return self._decode_with_atc_mi(mac, frame, advertisement_data)
            else:
                return self._decode_basic(mac, frame, advertisement_data)
                
        except Exception as e:
            logger.error(f"❌ Erro ao decodificar dados BLE {mac}: {e}")
            return None
    
    def _decode_with_atc_mi(self, mac: str, frame: bytes, advertisement_data) -> Optional[BLESensorData]:
        """Decodificar usando atc_mi_interface"""
        try:
            fmt_label, proc_frame = atc_mi_advertising_format(advertisement_data)
            if not proc_frame:
                return None
            
            mac_bytes = bytes.fromhex(mac.replace(":", ""))
            decoded = general_format.parse(proc_frame, mac_address=mac_bytes, bindkey=None)
            
            # Extrair temperatura e umidade
            temps = decoded.search_all("^temperature")
            hums = decoded.search_all("^humidity")
            batteries = decoded.search_all("^battery")
            
            temperature = temps[0] if temps else None
            humidity = hums[0] if hums else None
            battery = batteries[0] if batteries else None
            
            if temperature is not None and humidity is not None:
                return BLESensorData(
                    mac=mac,
                    temperature=temperature,
                    humidity=humidity,
                    battery=battery,
                    timestamp=datetime.now(),
                    rssi=getattr(advertisement_data, 'rssi', None)
                )
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro na decodificação atc_mi: {e}")
            return None
    
    def _decode_basic(self, mac: str, frame: bytes, advertisement_data) -> Optional[BLESensorData]:
        """Decodificação básica sem atc_mi_interface"""
        try:
            # Implementação básica para sensores Xiaomi
            if len(frame) >= 11:
                # Tentar decodificar dados básicos
                # Esta é uma implementação simplificada
                # Em produção, usar atc_mi_interface é recomendado
                
                # Verificar se é um sensor de temperatura/umidade
                if frame[0] == 0x16 and frame[1] == 0x95:  # UUID para temperatura/umidade
                    try:
                        # Decodificar temperatura (2 bytes)
                        temp_raw = int.from_bytes(frame[6:8], byteorder='little')
                        temperature = temp_raw / 100.0
                        
                        # Decodificar umidade (1 byte)
                        humidity = frame[8]
                        
                        return BLESensorData(
                            mac=mac,
                            temperature=temperature,
                            humidity=humidity,
                            battery=None,
                            timestamp=datetime.now(),
                            rssi=getattr(advertisement_data, 'rssi', None)
                        )
                    except Exception:
                        pass
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro na decodificação básica: {e}")
            return None
    
    def calculate_dew_point(self, temperature: float, humidity: float) -> Optional[float]:
        """Calcular ponto de orvalho"""
        try:
            if temperature is None or humidity is None:
                return None
            
            # Fórmula de Magnus
            a = 17.27
            b = 237.7
            gamma = math.log(humidity / 100.0) + (a * temperature) / (b + temperature)
            return (b * gamma) / (a - gamma)
            
        except Exception as e:
            logger.error(f"❌ Erro ao calcular ponto de orvalho: {e}")
            return None
    
    def get_sensor_data(self, mac: str) -> Optional[BLESensorData]:
        """Obter dados de um sensor específico"""
        return self.sensor_data.get(mac)
    
    def get_all_sensor_data(self) -> Dict[str, BLESensorData]:
        """Obter dados de todos os sensores"""
        return self.sensor_data.copy()
    
    def get_latest_data(self) -> Dict[str, Any]:
        """Obter dados mais recentes formatados"""
        data = {}
        for mac, sensor_data in self.latest_data.items():
            dew_point = self.calculate_dew_point(sensor_data.temperature, sensor_data.humidity)
            
            data[mac] = {
                'mac': mac,
                'name': self.known_sensors.get(mac, {}).get('name', 'Unknown'),
                'location': self.known_sensors.get(mac, {}).get('location', 'Unknown'),
                'temperature': sensor_data.temperature,
                'humidity': sensor_data.humidity,
                'dew_point': dew_point,
                'battery': sensor_data.battery,
                'rssi': sensor_data.rssi,
                'timestamp': sensor_data.timestamp.isoformat()
            }
        
        return data
    
    async def get_data_from_queue(self) -> Optional[BLESensorData]:
        """Obter dados da fila"""
        try:
            return await asyncio.wait_for(self.data_queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            return None
    
    def add_callback(self, callback: Callable[[BLESensorData], None]):
        """Adicionar callback para novos dados"""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[BLESensorData], None]):
        """Remover callback"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def is_active(self) -> bool:
        """Verificar se o coletor está ativo"""
        return self.running and BLE_SUPPORTED
    
    def get_known_sensors(self) -> Dict[str, Dict[str, str]]:
        """Obter lista de sensores conhecidos"""
        return self.known_sensors.copy()
    
    def add_known_sensor(self, mac: str, name: str, location: str = "Unknown"):
        """Adicionar sensor conhecido"""
        self.known_sensors[mac.upper()] = {
            "name": name,
            "location": location
        }
    
    def remove_known_sensor(self, mac: str):
        """Remover sensor conhecido"""
        mac_upper = mac.upper()
        if mac_upper in self.known_sensors:
            del self.known_sensors[mac_upper]
    
    async def stop(self):
        """Parar coletor"""
        try:
            logger.info("🛑 Parando coletor BLE")
            self.running = False
            logger.info("✅ Coletor BLE parado")
                
        except Exception as e:
            logger.error(f"❌ Erro ao parar coletor BLE: {e}")
    
    def get_device_info(self) -> Dict[str, Any]:
        """Obter informações do dispositivo"""
        return {
            'type': 'ble',
            'supported': BLE_SUPPORTED,
            'atc_mi_supported': ATC_MI_SUPPORTED,
            'known_sensors': len(self.known_sensors),
            'active_sensors': len(self.sensor_data),
            'active': self.is_active()
        }


