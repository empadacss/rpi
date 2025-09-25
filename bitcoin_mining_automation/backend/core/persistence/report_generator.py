"""
Gerador de relatórios e logs
Baseado no script original com funcionalidades de CSV e relatórios
"""

import asyncio
import logging
import csv
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from dataclasses import dataclass
import pandas as pd

logger = logging.getLogger(__name__)

@dataclass
class ReportConfig:
    """Configuração de relatório"""
    name: str
    description: str
    data_source: str
    fields: List[str]
    output_format: str  # csv, json, excel
    schedule: Optional[str] = None  # cron expression

class ReportGenerator:
    """Gerador de relatórios"""
    
    def __init__(self, config):
        self.config = config
        self.reports_dir = Path("reports")
        self.logs_dir = Path("logs")
        self.csv_dir = Path("logs_csv")
        
        # Criar diretórios
        self.reports_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        self.csv_dir.mkdir(exist_ok=True)
        
        # Configurações de relatórios
        self.report_configs = {
            'inverter': ReportConfig(
                name="Inversor",
                description="Relatório do inversor/exaustor",
                data_source="inverter",
                fields=["timestamp", "frequencia", "corrente", "temperatura", "estado"],
                output_format="csv"
            ),
            'multimedidor': ReportConfig(
                name="Multimedidor ABB",
                description="Relatório do multimedidor ABB",
                data_source="multimedidor",
                fields=["timestamp", "voltage_l1", "voltage_l2", "voltage_l3", "current_l1", "current_l2", "current_l3", "active_power_total", "frequency", "energy_ativa_direta"],
                output_format="csv"
            ),
            'ambiental': ReportConfig(
                name="Ambiental",
                description="Relatório de sensores ambientais",
                data_source="ambiental",
                fields=["timestamp", "sensor_mac", "temperature", "humidity", "dew_point"],
                output_format="csv"
            ),
            'f2pool': ReportConfig(
                name="F2Pool",
                description="Relatório da pool F2Pool",
                data_source="f2pool",
                fields=["timestamp", "hashrate", "h24_hashrate", "active_workers", "total_workers", "shares_accepted", "shares_rejected"],
                output_format="csv"
            ),
            'asic': ReportConfig(
                name="ASIC",
                description="Relatório dos ASICs",
                data_source="asic",
                fields=["timestamp", "miner_id", "ip_address", "model", "status", "hashrate", "power", "temperature", "fan_speed", "uptime", "errors", "efficiency"],
                output_format="csv"
            )
        }
    
    async def initialize(self):
        """Inicializar gerador de relatórios"""
        try:
            logger.info("📊 Inicializando gerador de relatórios")
            logger.info("✅ Gerador de relatórios inicializado com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar gerador de relatórios: {e}")
            raise
    
    async def save_inverter_data(self, data: Dict[str, Any]):
        """Salvar dados do inversor"""
        try:
            filename = self.csv_dir / "historico_inversor.csv"
            file_exists = filename.exists()
            
            with open(filename, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                if not file_exists:
                    writer.writerow(["Timestamp", "Frequencia", "Corrente", "Temperatura", "Estado"])
                
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                writer.writerow([
                    timestamp,
                    data.get('frequencia', '--'),
                    data.get('corrente', '--'),
                    data.get('temperatura', '--'),
                    data.get('estado', '--')
                ])
            
            logger.debug(f"📊 Dados do inversor salvos: {filename}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar dados do inversor: {e}")
    
    async def save_multimedidor_data(self, data: Dict[str, Any]):
        """Salvar dados do multimedidor ABB"""
        try:
            filename = self.csv_dir / "historico_multimedidor.csv"
            file_exists = filename.exists()
            
            with open(filename, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                if not file_exists:
                    writer.writerow([
                        "Timestamp", "Voltage L1", "Voltage L2", "Voltage L3",
                        "Current L1", "Current L2", "Current L3",
                        "Active Power Total", "Frequency", "Energy Ativa Direta"
                    ])
                
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                writer.writerow([
                    timestamp,
                    data.get('Voltage L1', '--'),
                    data.get('Voltage L2', '--'),
                    data.get('Voltage L3', '--'),
                    data.get('Current L1', '--'),
                    data.get('Current L2', '--'),
                    data.get('Current L3', '--'),
                    data.get('Active Power Total', '--'),
                    data.get('Frequency', '--'),
                    data.get('Energy Ativa Direta', '--')
                ])
            
            logger.debug(f"📊 Dados do multimedidor salvos: {filename}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar dados do multimedidor: {e}")
    
    async def save_ambiental_data(self, sensor_data: Dict[str, Any]):
        """Salvar dados ambientais"""
        try:
            filename = self.csv_dir / "historico_ambiental.csv"
            file_exists = filename.exists()
            
            with open(filename, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                if not file_exists:
                    writer.writerow([
                        "Timestamp", "Sensor MAC", "Temperature (°C)", "Humidity (%)", "Dew Point (°C)"
                    ])
                
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                for mac, data in sensor_data.items():
                    temperature = data.get('temperature')
                    humidity = data.get('humidity')
                    dew_point = self._calculate_dew_point(temperature, humidity)
                    
                    writer.writerow([
                        timestamp,
                        mac,
                        f"{temperature:.1f}" if temperature is not None else "--",
                        f"{humidity:.1f}" if humidity is not None else "--",
                        f"{dew_point:.1f}" if dew_point is not None else "--"
                    ])
            
            logger.debug(f"📊 Dados ambientais salvos: {filename}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar dados ambientais: {e}")
    
    async def save_f2pool_data(self, info_data: Dict[str, Any], workers_data: Dict[str, Any]):
        """Salvar dados da F2Pool"""
        try:
            filename = self.csv_dir / "historico_f2pool.csv"
            file_exists = filename.exists()
            
            with open(filename, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                if not file_exists:
                    writer.writerow(["Timestamp", "F2Pool Info", "Workers Info"])
                
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                writer.writerow([
                    timestamp,
                    json.dumps(info_data, separators=(",", ":")),
                    json.dumps(workers_data, separators=(",", ":"))
                ])
            
            logger.debug(f"📊 Dados F2Pool salvos: {filename}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar dados F2Pool: {e}")
    
    async def save_asic_data(self, data: Dict[str, Any]):
        """Salvar dados dos ASICs"""
        try:
            filename = self.csv_dir / "historico_asic.csv"
            file_exists = filename.exists()
            
            with open(filename, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                if not file_exists:
                    writer.writerow([
                        "Timestamp", "Miner ID", "IP Address", "Model", "Status",
                        "Hashrate", "Power", "Temperature", "Fan Speed",
                        "Uptime", "Errors", "Efficiency"
                    ])
                
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Salvar dados gerais
                if 'total_hashrate' in data:
                    writer.writerow([
                        timestamp, "SYSTEM", "ALL", "TOTAL", "SUMMARY",
                        data.get('total_hashrate', '--'),
                        data.get('total_power', '--'),
                        data.get('avg_temperature', '--'),
                        '--', '--', '--',
                        data.get('efficiency', '--')
                    ])
                
                # Salvar dados de cada minerador
                for miner_data in data.get('miners', []):
                    writer.writerow([
                        timestamp,
                        miner_data.get('id', '--'),
                        miner_data.get('ip', '--'),
                        miner_data.get('model', '--'),
                        miner_data.get('status', '--'),
                        miner_data.get('hashrate', '--'),
                        miner_data.get('power', '--'),
                        miner_data.get('temperature', '--'),
                        miner_data.get('fan_speed', '--'),
                        miner_data.get('uptime', '--'),
                        miner_data.get('errors', '--'),
                        miner_data.get('efficiency', '--')
                    ])
            
            logger.debug(f"📊 Dados ASIC salvos: {filename}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar dados ASIC: {e}")
    
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
    
    async def generate_report(self, report_type: str, start_date: Optional[datetime] = None, 
                            end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Gerar relatório"""
        try:
            if report_type not in self.report_configs:
                raise ValueError(f"Tipo de relatório inválido: {report_type}")
            
            config = self.report_configs[report_type]
            
            # Definir datas padrão
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=1)
            
            # Carregar dados
            data = await self._load_report_data(report_type, start_date, end_date)
            
            # Gerar relatório
            report = {
                'type': report_type,
                'name': config.name,
                'description': config.description,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'generated_at': datetime.now().isoformat(),
                'data': data,
                'summary': self._generate_summary(data, report_type)
            }
            
            # Salvar relatório
            await self._save_report(report)
            
            logger.info(f"📊 Relatório {report_type} gerado com sucesso")
            return report
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar relatório {report_type}: {e}")
            raise
    
    async def _load_report_data(self, report_type: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Carregar dados para relatório"""
        try:
            filename = self.csv_dir / f"historico_{report_type}.csv"
            
            if not filename.exists():
                return []
            
            data = []
            with open(filename, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        # Converter timestamp
                        timestamp = datetime.strptime(row['Timestamp'], "%Y-%m-%d %H:%M:%S")
                        
                        # Filtrar por data
                        if start_date <= timestamp <= end_date:
                            data.append(row)
                    except Exception as e:
                        logger.warning(f"⚠️ Erro ao processar linha do CSV: {e}")
                        continue
            
            return data
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar dados do relatório: {e}")
            return []
    
    def _generate_summary(self, data: List[Dict[str, Any]], report_type: str) -> Dict[str, Any]:
        """Gerar resumo do relatório"""
        try:
            if not data:
                return {}
            
            summary = {
                'total_records': len(data),
                'date_range': {
                    'start': data[0]['Timestamp'] if data else None,
                    'end': data[-1]['Timestamp'] if data else None
                }
            }
            
            if report_type == 'inverter':
                # Resumo do inversor
                frequencies = [float(row['Frequencia']) for row in data if row['Frequencia'] != '--']
                currents = [float(row['Corrente']) for row in data if row['Corrente'] != '--']
                temperatures = [float(row['Temperatura']) for row in data if row['Temperatura'] != '--']
                
                summary.update({
                    'avg_frequency': sum(frequencies) / len(frequencies) if frequencies else 0,
                    'avg_current': sum(currents) / len(currents) if currents else 0,
                    'avg_temperature': sum(temperatures) / len(temperatures) if temperatures else 0,
                    'max_temperature': max(temperatures) if temperatures else 0,
                    'min_temperature': min(temperatures) if temperatures else 0
                })
            
            elif report_type == 'ambiental':
                # Resumo ambiental
                temperatures = []
                humidities = []
                dew_points = []
                
                for row in data:
                    if row['Temperature (°C)'] != '--':
                        temperatures.append(float(row['Temperature (°C)']))
                    if row['Humidity (%)'] != '--':
                        humidities.append(float(row['Humidity (%)']))
                    if row['Dew Point (°C)'] != '--':
                        dew_points.append(float(row['Dew Point (°C)']))
                
                summary.update({
                    'avg_temperature': sum(temperatures) / len(temperatures) if temperatures else 0,
                    'max_temperature': max(temperatures) if temperatures else 0,
                    'min_temperature': min(temperatures) if temperatures else 0,
                    'avg_humidity': sum(humidities) / len(humidities) if humidities else 0,
                    'max_humidity': max(humidities) if humidities else 0,
                    'min_humidity': min(humidities) if humidities else 0,
                    'avg_dew_point': sum(dew_points) / len(dew_points) if dew_points else 0
                })
            
            elif report_type == 'f2pool':
                # Resumo F2Pool
                hashrates = []
                workers = []
                
                for row in data:
                    try:
                        info = json.loads(row['F2Pool Info'])
                        if 'info' in info and 'hash_rate' in info['info']:
                            hashrates.append(info['info']['hash_rate'] / 1e12)  # Converter para TH/s
                        
                        workers_info = json.loads(row['Workers Info'])
                        if 'workers' in workers_info:
                            workers.append(len(workers_info['workers']))
                    except Exception:
                        continue
                
                summary.update({
                    'avg_hashrate_th_s': sum(hashrates) / len(hashrates) if hashrates else 0,
                    'max_hashrate_th_s': max(hashrates) if hashrates else 0,
                    'min_hashrate_th_s': min(hashrates) if hashrates else 0,
                    'avg_workers': sum(workers) / len(workers) if workers else 0
                })
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar resumo: {e}")
            return {}
    
    async def _save_report(self, report: Dict[str, Any]):
        """Salvar relatório"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self.reports_dir / f"report_{report['type']}_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📊 Relatório salvo: {filename}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar relatório: {e}")
    
    async def export_to_csv(self, report_type: str, start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None) -> str:
        """Exportar relatório para CSV"""
        try:
            # Gerar relatório
            report = await self.generate_report(report_type, start_date, end_date)
            
            # Salvar como CSV
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self.reports_dir / f"report_{report_type}_{timestamp}.csv"
            
            if report['data']:
                df = pd.DataFrame(report['data'])
                df.to_csv(filename, index=False, encoding='utf-8')
            
            logger.info(f"📊 Relatório CSV exportado: {filename}")
            return str(filename)
            
        except Exception as e:
            logger.error(f"❌ Erro ao exportar CSV: {e}")
            raise
    
    async def get_available_reports(self) -> List[Dict[str, Any]]:
        """Obter relatórios disponíveis"""
        try:
            reports = []
            
            for report_type, config in self.report_configs.items():
                filename = self.csv_dir / f"historico_{report_type}.csv"
                
                if filename.exists():
                    # Obter estatísticas do arquivo
                    with open(filename, 'r', encoding='utf-8') as f:
                        reader = csv.reader(f)
                        rows = list(reader)
                    
                    if len(rows) > 1:  # Mais que cabeçalho
                        first_row = rows[1]
                        last_row = rows[-1]
                        
                        reports.append({
                            'type': report_type,
                            'name': config.name,
                            'description': config.description,
                            'records': len(rows) - 1,
                            'first_record': first_row[0] if first_row else None,
                            'last_record': last_row[0] if last_row else None,
                            'file_size': filename.stat().st_size
                        })
            
            return reports
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter relatórios disponíveis: {e}")
            return []
    
    async def cleanup_old_data(self, days: int = 30):
        """Limpar dados antigos"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            cleaned_files = []
            
            for report_type in self.report_configs.keys():
                filename = self.csv_dir / f"historico_{report_type}.csv"
                
                if filename.exists():
                    # Ler arquivo e filtrar dados recentes
                    with open(filename, 'r', encoding='utf-8') as f:
                        reader = csv.reader(f)
                        rows = list(reader)
                    
                    if len(rows) > 1:
                        header = rows[0]
                        recent_rows = [header]  # Manter cabeçalho
                        
                        for row in rows[1:]:
                            try:
                                timestamp = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
                                if timestamp > cutoff_date:
                                    recent_rows.append(row)
                            except Exception:
                                recent_rows.append(row)  # Manter linha com erro
                        
                        # Reescrever arquivo se houver dados removidos
                        if len(recent_rows) < len(rows):
                            with open(filename, 'w', newline='', encoding='utf-8') as f:
                                writer = csv.writer(f)
                                writer.writerows(recent_rows)
                            
                            cleaned_files.append(str(filename))
            
            logger.info(f"🧹 Limpeza concluída: {len(cleaned_files)} arquivos processados")
            return cleaned_files
            
        except Exception as e:
            logger.error(f"❌ Erro na limpeza de dados: {e}")
            return []
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Obter informações de armazenamento"""
        try:
            total_size = 0
            file_count = 0
            
            for directory in [self.csv_dir, self.reports_dir, self.logs_dir]:
                if directory.exists():
                    for file_path in directory.iterdir():
                        if file_path.is_file():
                            total_size += file_path.stat().st_size
                            file_count += 1
            
            return {
                'total_size_bytes': total_size,
                'total_size_mb': total_size / (1024 * 1024),
                'file_count': file_count,
                'csv_dir': str(self.csv_dir),
                'reports_dir': str(self.reports_dir),
                'logs_dir': str(self.logs_dir)
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter informações de armazenamento: {e}")
            return {}


