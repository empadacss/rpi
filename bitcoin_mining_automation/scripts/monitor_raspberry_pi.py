#!/usr/bin/env python3
"""
Script de monitoramento específico para Raspberry Pi
Sistema de Automação para Mineração de Bitcoin
"""

import asyncio
import logging
import sys
import os
import json
import time
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from backend.core.config import Config
from backend.core.system_manager import SystemManager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/monitor_raspberry_pi.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class RaspberryPiMonitor:
    """Classe para monitorar o sistema no Raspberry Pi"""
    
    def __init__(self):
        self.config = None
        self.system_manager = None
        self.monitoring_data = {}
        self.alerts = []
        self.start_time = datetime.now()
        
    async def initialize(self):
        """Inicializar sistema de monitoramento"""
        try:
            logger.info("Inicializando sistema de monitoramento...")
            
            # Carregar configuração
            self.config = Config()
            
            # Inicializar system manager
            self.system_manager = SystemManager(self.config)
            await self.system_manager.initialize()
            
            logger.info("Sistema de monitoramento inicializado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao inicializar sistema de monitoramento: {e}")
            return False
    
    def get_system_info(self) -> Dict[str, Any]:
        """Obter informações do sistema"""
        try:
            # Informações básicas do sistema
            system_info = {
                "hostname": os.uname().nodename,
                "platform": os.uname().sysname,
                "architecture": os.uname().machine,
                "uptime": self.get_uptime(),
                "load_average": os.getloadavg(),
                "memory": self.get_memory_info(),
                "disk": self.get_disk_info(),
                "cpu": self.get_cpu_info(),
                "temperature": self.get_temperature(),
                "network": self.get_network_info(),
                "timestamp": datetime.now().isoformat()
            }
            
            return system_info
            
        except Exception as e:
            logger.error(f"Erro ao obter informações do sistema: {e}")
            return {}
    
    def get_uptime(self) -> str:
        """Obter tempo de atividade do sistema"""
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.readline().split()[0])
            
            uptime = timedelta(seconds=uptime_seconds)
            return str(uptime)
            
        except Exception as e:
            logger.error(f"Erro ao obter uptime: {e}")
            return "N/A"
    
    def get_memory_info(self) -> Dict[str, Any]:
        """Obter informações de memória"""
        try:
            with open('/proc/meminfo', 'r') as f:
                meminfo = {}
                for line in f:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        meminfo[key.strip()] = value.strip()
            
            total = int(meminfo['MemTotal'].split()[0])
            available = int(meminfo['MemAvailable'].split()[0])
            used = total - available
            
            return {
                "total": total,
                "used": used,
                "available": available,
                "percentage": (used / total) * 100
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter informações de memória: {e}")
            return {}
    
    def get_disk_info(self) -> Dict[str, Any]:
        """Obter informações de disco"""
        try:
            result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True)
            lines = result.stdout.strip().split('\n')
            
            if len(lines) > 1:
                parts = lines[1].split()
                return {
                    "total": parts[1],
                    "used": parts[2],
                    "available": parts[3],
                    "percentage": parts[4].replace('%', '')
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Erro ao obter informações de disco: {e}")
            return {}
    
    def get_cpu_info(self) -> Dict[str, Any]:
        """Obter informações de CPU"""
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = {}
                for line in f:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        cpuinfo[key.strip()] = value.strip()
            
            # Contar cores
            cpu_count = len([line for line in open('/proc/cpuinfo') if line.startswith('processor')])
            
            # Obter uso de CPU
            with open('/proc/stat', 'r') as f:
                cpu_stats = f.readline().split()
            
            # Calcular uso de CPU (simplificado)
            user = int(cpu_stats[1])
            nice = int(cpu_stats[2])
            system = int(cpu_stats[3])
            idle = int(cpu_stats[4])
            
            total = user + nice + system + idle
            cpu_usage = ((total - idle) / total) * 100
            
            return {
                "model": cpuinfo.get('model name', 'N/A'),
                "cores": cpu_count,
                "usage": cpu_usage
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter informações de CPU: {e}")
            return {}
    
    def get_temperature(self) -> Dict[str, Any]:
        """Obter temperatura do sistema"""
        try:
            temperature = {}
            
            # Temperatura da CPU
            if Path('/sys/class/thermal/thermal_zone0/temp').exists():
                with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                    temp_millicelsius = int(f.read().strip())
                    temp_celsius = temp_millicelsius / 1000
                    temperature['cpu'] = temp_celsius
            
            # Temperatura do GPU (se disponível)
            if Path('/opt/vc/bin/vcgencmd').exists():
                result = subprocess.run(['/opt/vc/bin/vcgencmd', 'measure_temp'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    temp_str = result.stdout.strip()
                    temp_value = float(temp_str.split('=')[1].replace("'C", ""))
                    temperature['gpu'] = temp_value
            
            return temperature
            
        except Exception as e:
            logger.error(f"Erro ao obter temperatura: {e}")
            return {}
    
    def get_network_info(self) -> Dict[str, Any]:
        """Obter informações de rede"""
        try:
            network_info = {}
            
            # Interfaces de rede
            result = subprocess.run(['ip', 'addr', 'show'], capture_output=True, text=True)
            interfaces = []
            
            for line in result.stdout.split('\n'):
                if 'inet ' in line and '127.0.0.1' not in line:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        ip = parts[1].split('/')[0]
                        interfaces.append(ip)
            
            network_info['interfaces'] = interfaces
            
            # Conectividade
            try:
                result = subprocess.run(['ping', '-c', '1', '8.8.8.8'], 
                                      capture_output=True, text=True, timeout=5)
                network_info['connectivity'] = result.returncode == 0
            except subprocess.TimeoutExpired:
                network_info['connectivity'] = False
            
            return network_info
            
        except Exception as e:
            logger.error(f"Erro ao obter informações de rede: {e}")
            return {}
    
    def get_docker_status(self) -> Dict[str, Any]:
        """Obter status dos containers Docker"""
        try:
            result = subprocess.run(['docker', 'ps', '--format', 'json'], 
                                  capture_output=True, text=True)
            
            containers = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        container = json.loads(line)
                        containers.append({
                            "name": container.get('Names', 'N/A'),
                            "status": container.get('Status', 'N/A'),
                            "ports": container.get('Ports', 'N/A')
                        })
                    except json.JSONDecodeError:
                        continue
            
            return {"containers": containers}
            
        except Exception as e:
            logger.error(f"Erro ao obter status do Docker: {e}")
            return {}
    
    def get_service_status(self) -> Dict[str, Any]:
        """Obter status dos serviços"""
        try:
            services = {}
            
            # Serviços do sistema
            systemd_services = [
                'bitcoin-mining.service',
                'bitcoin-mining-python.service',
                'docker.service',
                'bluetooth.service'
            ]
            
            for service in systemd_services:
                try:
                    result = subprocess.run(['systemctl', 'is-active', service], 
                                          capture_output=True, text=True)
                    services[service] = result.stdout.strip()
                except Exception:
                    services[service] = 'unknown'
            
            return services
            
        except Exception as e:
            logger.error(f"Erro ao obter status dos serviços: {e}")
            return {}
    
    def get_application_status(self) -> Dict[str, Any]:
        """Obter status da aplicação"""
        try:
            if not self.system_manager:
                return {"status": "not_initialized"}
            
            # Status dos coletores
            collectors_status = {}
            for name, collector in self.system_manager.collectors.items():
                if hasattr(collector, 'is_connected'):
                    collectors_status[name] = collector.is_connected()
                else:
                    collectors_status[name] = "unknown"
            
            # Status dos gerenciadores
            managers_status = {}
            for name, manager in self.system_manager.managers.items():
                if hasattr(manager, 'is_healthy'):
                    managers_status[name] = manager.is_healthy()
                else:
                    managers_status[name] = "unknown"
            
            return {
                "status": "running" if self.system_manager.running else "stopped",
                "collectors": collectors_status,
                "managers": managers_status,
                "uptime": str(datetime.now() - self.start_time)
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter status da aplicação: {e}")
            return {"status": "error", "error": str(e)}
    
    def get_logs_summary(self) -> Dict[str, Any]:
        """Obter resumo dos logs"""
        try:
            logs_path = Path("logs")
            if not logs_path.exists():
                return {"error": "Diretório de logs não encontrado"}
            
            log_files = list(logs_path.glob("*.log"))
            logs_summary = {}
            
            for log_file in log_files:
                try:
                    # Contar linhas
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                    
                    # Contar níveis de log
                    error_count = len([line for line in lines if 'ERROR' in line])
                    warning_count = len([line for line in lines if 'WARNING' in line])
                    info_count = len([line for line in lines if 'INFO' in line])
                    
                    logs_summary[log_file.name] = {
                        "total_lines": len(lines),
                        "errors": error_count,
                        "warnings": warning_count,
                        "info": info_count,
                        "last_modified": datetime.fromtimestamp(log_file.stat().st_mtime).isoformat()
                    }
                    
                except Exception as e:
                    logs_summary[log_file.name] = {"error": str(e)}
            
            return logs_summary
            
        except Exception as e:
            logger.error(f"Erro ao obter resumo dos logs: {e}")
            return {"error": str(e)}
    
    def check_alerts(self) -> List[Dict[str, Any]]:
        """Verificar alertas"""
        alerts = []
        
        try:
            # Verificar temperatura
            temp_info = self.get_temperature()
            if 'cpu' in temp_info and temp_info['cpu'] > 80:
                alerts.append({
                    "type": "temperature",
                    "level": "critical",
                    "message": f"Temperatura da CPU alta: {temp_info['cpu']}°C",
                    "timestamp": datetime.now().isoformat()
                })
            
            # Verificar memória
            mem_info = self.get_memory_info()
            if mem_info.get('percentage', 0) > 90:
                alerts.append({
                    "type": "memory",
                    "level": "warning",
                    "message": f"Uso de memória alto: {mem_info['percentage']:.1f}%",
                    "timestamp": datetime.now().isoformat()
                })
            
            # Verificar disco
            disk_info = self.get_disk_info()
            if disk_info.get('percentage', '0').replace('%', ''):
                disk_usage = float(disk_info['percentage'].replace('%', ''))
                if disk_usage > 90:
                    alerts.append({
                        "type": "disk",
                        "level": "critical",
                        "message": f"Uso de disco alto: {disk_usage}%",
                        "timestamp": datetime.now().isoformat()
                    })
            
            # Verificar conectividade
            network_info = self.get_network_info()
            if not network_info.get('connectivity', False):
                alerts.append({
                    "type": "network",
                    "level": "warning",
                    "message": "Sem conectividade com a internet",
                    "timestamp": datetime.now().isoformat()
                })
            
            # Verificar serviços
            services = self.get_service_status()
            for service, status in services.items():
                if status not in ['active', 'running']:
                    alerts.append({
                        "type": "service",
                        "level": "warning",
                        "message": f"Serviço {service} não está ativo: {status}",
                        "timestamp": datetime.now().isoformat()
                    })
            
        except Exception as e:
            logger.error(f"Erro ao verificar alertas: {e}")
            alerts.append({
                "type": "system",
                "level": "error",
                "message": f"Erro ao verificar alertas: {e}",
                "timestamp": datetime.now().isoformat()
            })
        
        return alerts
    
    def generate_report(self) -> Dict[str, Any]:
        """Gerar relatório completo"""
        try:
            report = {
                "timestamp": datetime.now().isoformat(),
                "system": self.get_system_info(),
                "docker": self.get_docker_status(),
                "services": self.get_service_status(),
                "application": self.get_application_status(),
                "logs": self.get_logs_summary(),
                "alerts": self.check_alerts()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
    
    def save_report(self, report: Dict[str, Any]):
        """Salvar relatório"""
        try:
            reports_path = Path("reports")
            reports_path.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = reports_path / f"monitor_report_{timestamp}.json"
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Relatório salvo em: {report_file}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar relatório: {e}")
    
    def print_summary(self, report: Dict[str, Any]):
        """Imprimir resumo do relatório"""
        print("\n" + "="*60)
        print("RELATÓRIO DE MONITORAMENTO - RASPBERRY PI")
        print("="*60)
        print(f"Data: {report['timestamp']}")
        print()
        
        # Sistema
        system = report.get('system', {})
        print("SISTEMA:")
        print(f"  Hostname: {system.get('hostname', 'N/A')}")
        print(f"  Uptime: {system.get('uptime', 'N/A')}")
        print(f"  Load Average: {system.get('load_average', 'N/A')}")
        
        # CPU
        cpu = system.get('cpu', {})
        print(f"  CPU: {cpu.get('model', 'N/A')}")
        print(f"  Cores: {cpu.get('cores', 'N/A')}")
        print(f"  Uso: {cpu.get('usage', 0):.1f}%")
        
        # Memória
        memory = system.get('memory', {})
        if memory:
            print(f"  Memória: {memory.get('used', 0)}/{memory.get('total', 0)} KB ({memory.get('percentage', 0):.1f}%)")
        
        # Disco
        disk = system.get('disk', {})
        if disk:
            print(f"  Disco: {disk.get('used', 'N/A')}/{disk.get('total', 'N/A')} ({disk.get('percentage', 'N/A')})")
        
        # Temperatura
        temp = system.get('temperature', {})
        if temp:
            for key, value in temp.items():
                print(f"  Temperatura {key.upper()}: {value}°C")
        
        print()
        
        # Aplicação
        app = report.get('application', {})
        print("APLICAÇÃO:")
        print(f"  Status: {app.get('status', 'N/A')}")
        print(f"  Uptime: {app.get('uptime', 'N/A')}")
        
        # Coletores
        collectors = app.get('collectors', {})
        if collectors:
            print("  Coletores:")
            for name, status in collectors.items():
                print(f"    {name}: {status}")
        
        # Gerenciadores
        managers = app.get('managers', {})
        if managers:
            print("  Gerenciadores:")
            for name, status in managers.items():
                print(f"    {name}: {status}")
        
        print()
        
        # Alertas
        alerts = report.get('alerts', [])
        if alerts:
            print("ALERTAS:")
            for alert in alerts:
                level = alert.get('level', 'info').upper()
                message = alert.get('message', 'N/A')
                print(f"  [{level}] {message}")
        else:
            print("ALERTAS: Nenhum")
        
        print()
        
        # Serviços
        services = report.get('services', {})
        if services:
            print("SERVIÇOS:")
            for service, status in services.items():
                print(f"  {service}: {status}")
        
        print()
        
        # Docker
        docker = report.get('docker', {})
        containers = docker.get('containers', [])
        if containers:
            print("CONTAINERS DOCKER:")
            for container in containers:
                name = container.get('name', 'N/A')
                status = container.get('status', 'N/A')
                print(f"  {name}: {status}")
        
        print("="*60)
    
    async def run_monitoring(self, interval: int = 60):
        """Executar monitoramento contínuo"""
        logger.info(f"Iniciando monitoramento com intervalo de {interval} segundos...")
        
        try:
            while True:
                # Gerar relatório
                report = self.generate_report()
                
                # Salvar relatório
                self.save_report(report)
                
                # Imprimir resumo
                self.print_summary(report)
                
                # Aguardar próximo ciclo
                await asyncio.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("Monitoramento interrompido pelo usuário")
        except Exception as e:
            logger.error(f"Erro durante o monitoramento: {e}")

async def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor do Sistema de Mineração - Raspberry Pi')
    parser.add_argument('--interval', '-i', type=int, default=60, 
                       help='Intervalo de monitoramento em segundos (padrão: 60)')
    parser.add_argument('--once', '-o', action='store_true', 
                       help='Executar apenas uma vez')
    parser.add_argument('--quiet', '-q', action='store_true', 
                       help='Modo silencioso (apenas logs)')
    
    args = parser.parse_args()
    
    # Configurar logging
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    
    # Criar diretório de logs se não existir
    os.makedirs("logs", exist_ok=True)
    
    # Inicializar monitor
    monitor = RaspberryPiMonitor()
    
    # Inicializar sistema
    if not await monitor.initialize():
        logger.error("Falha ao inicializar sistema de monitoramento")
        return
    
    try:
        if args.once:
            # Executar apenas uma vez
            report = monitor.generate_report()
            monitor.save_report(report)
            if not args.quiet:
                monitor.print_summary(report)
        else:
            # Executar monitoramento contínuo
            await monitor.run_monitoring(args.interval)
            
    except Exception as e:
        logger.error(f"Erro durante execução: {e}")
    finally:
        # Fechar sistema
        if monitor.system_manager:
            await monitor.system_manager.shutdown()

if __name__ == "__main__":
    asyncio.run(main())


