#!/usr/bin/env python3
"""
Script de diagnóstico específico para Raspberry Pi com Ubuntu
Sistema de Automação para Mineração de Bitcoin
"""

import os
import sys
import json
import subprocess
import platform
import psutil
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

class UbuntuRaspberryPiDiagnostic:
    """Classe para diagnóstico do sistema no Raspberry Pi com Ubuntu"""
    
    def __init__(self):
        self.base_path = Path("/opt/bitcoin_mining")
        self.diagnostic_results = {}
        self.issues = []
        self.recommendations = []
        
    def check_system_info(self) -> Dict[str, Any]:
        """Verificar informações do sistema"""
        try:
            info = {
                "hostname": platform.node(),
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "python_version": platform.python_version(),
                "architecture": platform.architecture(),
                "timestamp": datetime.now().isoformat()
            }
            
            # Informações específicas do Ubuntu
            try:
                with open('/etc/os-release', 'r') as f:
                    os_info = {}
                    for line in f:
                        if '=' in line:
                            key, value = line.strip().split('=', 1)
                            os_info[key] = value.strip('"')
                    info["os_info"] = os_info
            except Exception as e:
                info["os_info"] = {"error": str(e)}
            
            return info
            
        except Exception as e:
            return {"error": str(e)}
    
    def check_hardware(self) -> Dict[str, Any]:
        """Verificar hardware"""
        try:
            hardware = {
                "cpu_count": psutil.cpu_count(),
                "cpu_freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
                "memory": psutil.virtual_memory()._asdict(),
                "disk": psutil.disk_usage('/')._asdict(),
                "temperature": self.get_temperature(),
                "gpio_available": self.check_gpio(),
                "bluetooth_available": self.check_bluetooth()
            }
            
            return hardware
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_temperature(self) -> Dict[str, Any]:
        """Obter temperatura do sistema"""
        try:
            temp_info = {}
            
            # Temperatura da CPU
            if Path('/sys/class/thermal/thermal_zone0/temp').exists():
                with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                    temp_millicelsius = int(f.read().strip())
                    temp_celsius = temp_millicelsius / 1000
                    temp_info['cpu'] = temp_celsius
            
            # Temperatura do GPU (se disponível)
            if Path('/opt/vc/bin/vcgencmd').exists():
                try:
                    result = subprocess.run(['/opt/vc/bin/vcgencmd', 'measure_temp'], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        temp_str = result.stdout.strip()
                        temp_value = float(temp_str.split('=')[1].replace("'C", ""))
                        temp_info['gpu'] = temp_value
                except Exception:
                    pass
            
            return temp_info
            
        except Exception as e:
            return {"error": str(e)}
    
    def check_gpio(self) -> bool:
        """Verificar se GPIO está disponível"""
        try:
            return Path('/sys/class/gpio').exists()
        except Exception:
            return False
    
    def check_bluetooth(self) -> bool:
        """Verificar se Bluetooth está disponível"""
        try:
            result = subprocess.run(['bluetoothctl', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except Exception:
            return False
    
    def check_dependencies(self) -> Dict[str, Any]:
        """Verificar dependências"""
        try:
            dependencies = {}
            
            # Python
            dependencies["python"] = {
                "version": sys.version,
                "executable": sys.executable,
                "path": sys.path
            }
            
            # Docker
            try:
                result = subprocess.run(['docker', '--version'], 
                                      capture_output=True, text=True, timeout=5)
                dependencies["docker"] = {
                    "available": result.returncode == 0,
                    "version": result.stdout.strip() if result.returncode == 0 else None
                }
            except Exception as e:
                dependencies["docker"] = {"available": False, "error": str(e)}
            
            # Docker Compose
            try:
                result = subprocess.run(['docker-compose', '--version'], 
                                      capture_output=True, text=True, timeout=5)
                dependencies["docker_compose"] = {
                    "available": result.returncode == 0,
                    "version": result.stdout.strip() if result.returncode == 0 else None
                }
            except Exception as e:
                dependencies["docker_compose"] = {"available": False, "error": str(e)}
            
            # Node.js
            try:
                result = subprocess.run(['node', '--version'], 
                                      capture_output=True, text=True, timeout=5)
                dependencies["nodejs"] = {
                    "available": result.returncode == 0,
                    "version": result.stdout.strip() if result.returncode == 0 else None
                }
            except Exception as e:
                dependencies["nodejs"] = {"available": False, "error": str(e)}
            
            # HashCore Toolkit
            try:
                result = subprocess.run(['hashcore', '--version'], 
                                      capture_output=True, text=True, timeout=5)
                dependencies["hashcore"] = {
                    "available": result.returncode == 0,
                    "version": result.stdout.strip() if result.returncode == 0 else None
                }
            except Exception as e:
                dependencies["hashcore"] = {"available": False, "error": str(e)}
            
            # Python packages
            try:
                import pkg_resources
                packages = {}
                required_packages = [
                    'fastapi', 'uvicorn', 'pydantic', 'sqlalchemy', 
                    'psycopg2-binary', 'redis', 'pymodbus', 'requests',
                    'httpx', 'schedule', 'tenacity', 'pandas', 'numpy',
                    'matplotlib', 'seaborn', 'plotly', 'bleak', 'ttkbootstrap',
                    'pillow', 'scikit-learn', 'scipy', 'opencv-python',
                    'prometheus-client', 'structlog', 'loguru'
                ]
                
                for package in required_packages:
                    try:
                        version = pkg_resources.get_distribution(package).version
                        packages[package] = {"available": True, "version": version}
                    except pkg_resources.DistributionNotFound:
                        packages[package] = {"available": False, "version": None}
                
                dependencies["python_packages"] = packages
                
            except Exception as e:
                dependencies["python_packages"] = {"error": str(e)}
            
            return dependencies
            
        except Exception as e:
            return {"error": str(e)}
    
    def check_network(self) -> Dict[str, Any]:
        """Verificar configuração de rede"""
        try:
            network = {}
            
            # Interfaces de rede
            try:
                result = subprocess.run(['ip', 'addr', 'show'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    interfaces = []
                    for line in result.stdout.split('\n'):
                        if 'inet ' in line and '127.0.0.1' not in line:
                            parts = line.strip().split()
                            if len(parts) >= 2:
                                ip = parts[1].split('/')[0]
                                interfaces.append(ip)
                    network["interfaces"] = interfaces
            except Exception as e:
                network["interfaces"] = {"error": str(e)}
            
            # Conectividade
            try:
                result = subprocess.run(['ping', '-c', '1', '8.8.8.8'], 
                                      capture_output=True, text=True, timeout=10)
                network["connectivity"] = result.returncode == 0
            except Exception as e:
                network["connectivity"] = False
                network["connectivity_error"] = str(e)
            
            # Portas abertas
            try:
                result = subprocess.run(['ss', '-tuln'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    ports = []
                    for line in result.stdout.split('\n'):
                        if ':' in line:
                            parts = line.split()
                            if len(parts) >= 4:
                                local = parts[3]
                                if ':' in local:
                                    port = local.split(':')[-1]
                                    ports.append(port)
                    network["open_ports"] = ports
            except Exception as e:
                network["open_ports"] = {"error": str(e)}
            
            return network
            
        except Exception as e:
            return {"error": str(e)}
    
    def check_services(self) -> Dict[str, Any]:
        """Verificar serviços do sistema"""
        try:
            services = {}
            
            # Serviços systemd
            systemd_services = [
                'bitcoin-mining.service',
                'bitcoin-mining-python.service',
                'docker.service',
                'bluetooth.service'
            ]
            
            for service in systemd_services:
                try:
                    result = subprocess.run(['systemctl', 'is-active', service], 
                                          capture_output=True, text=True, timeout=5)
                    services[service] = result.stdout.strip()
                except Exception as e:
                    services[service] = f"error: {e}"
            
            # Docker containers
            try:
                result = subprocess.run(['docker', 'ps', '--format', 'json'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
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
                    services["docker_containers"] = containers
            except Exception as e:
                services["docker_containers"] = {"error": str(e)}
            
            return services
            
        except Exception as e:
            return {"error": str(e)}
    
    def check_application(self) -> Dict[str, Any]:
        """Verificar aplicação"""
        try:
            app_info = {}
            
            # Verificar se diretório existe
            app_info["directory_exists"] = self.base_path.exists()
            
            # Verificar arquivos importantes
            important_files = [
                "main.py",
                "docker-compose.yml",
                "requirements.txt",
                ".env",
                "config/devices.yaml"
            ]
            
            files_status = {}
            for file_path in important_files:
                full_path = self.base_path / file_path
                files_status[file_path] = {
                    "exists": full_path.exists(),
                    "size": full_path.stat().st_size if full_path.exists() else 0
                }
            app_info["files"] = files_status
            
            # Verificar logs
            logs_path = self.base_path / "logs"
            if logs_path.exists():
                log_files = list(logs_path.glob("*.log"))
                app_info["logs"] = {
                    "count": len(log_files),
                    "files": [f.name for f in log_files]
                }
            else:
                app_info["logs"] = {"count": 0, "files": []}
            
            # Verificar permissões
            app_info["permissions"] = {
                "readable": os.access(self.base_path, os.R_OK),
                "writable": os.access(self.base_path, os.W_OK),
                "executable": os.access(self.base_path, os.X_OK)
            }
            
            return app_info
            
        except Exception as e:
            return {"error": str(e)}
    
    def check_performance(self) -> Dict[str, Any]:
        """Verificar performance do sistema"""
        try:
            performance = {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "load_average": os.getloadavg(),
                "uptime": self.get_uptime()
            }
            
            return performance
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_uptime(self) -> str:
        """Obter tempo de atividade do sistema"""
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.readline().split()[0])
            
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            
            return f"{days}d {hours}h {minutes}m"
            
        except Exception as e:
            return f"error: {e}"
    
    def analyze_issues(self) -> List[str]:
        """Analisar problemas encontrados"""
        issues = []
        
        # Verificar dependências
        deps = self.diagnostic_results.get("dependencies", {})
        
        if not deps.get("docker", {}).get("available", False):
            issues.append("Docker não está disponível")
        
        if not deps.get("docker_compose", {}).get("available", False):
            issues.append("Docker Compose não está disponível")
        
        if not deps.get("nodejs", {}).get("available", False):
            issues.append("Node.js não está disponível")
        
        # Verificar hardware
        hardware = self.diagnostic_results.get("hardware", {})
        
        memory = hardware.get("memory", {})
        if memory.get("percent", 0) > 90:
            issues.append(f"Uso de memória alto: {memory.get('percent', 0):.1f}%")
        
        disk = hardware.get("disk", {})
        if disk.get("percent", 0) > 90:
            issues.append(f"Uso de disco alto: {disk.get('percent', 0):.1f}%")
        
        temp = hardware.get("temperature", {})
        if temp.get("cpu", 0) > 80:
            issues.append(f"Temperatura da CPU alta: {temp.get('cpu', 0):.1f}°C")
        
        # Verificar rede
        network = self.diagnostic_results.get("network", {})
        
        if not network.get("connectivity", False):
            issues.append("Sem conectividade com a internet")
        
        # Verificar aplicação
        app = self.diagnostic_results.get("application", {})
        
        if not app.get("directory_exists", False):
            issues.append("Diretório da aplicação não existe")
        
        files = app.get("files", {})
        if not files.get(".env", {}).get("exists", False):
            issues.append("Arquivo .env não encontrado")
        
        if not files.get("config/devices.yaml", {}).get("exists", False):
            issues.append("Configuração de dispositivos não encontrada")
        
        return issues
    
    def generate_recommendations(self) -> List[str]:
        """Gerar recomendações"""
        recommendations = []
        
        # Recomendações baseadas em problemas
        issues = self.analyze_issues()
        
        if "Docker não está disponível" in issues:
            recommendations.append("Instale Docker: curl -fsSL https://get.docker.com | sh")
        
        if "Docker Compose não está disponível" in issues:
            recommendations.append("Instale Docker Compose: sudo apt install docker-compose")
        
        if "Node.js não está disponível" in issues:
            recommendations.append("Instale Node.js: curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt-get install -y nodejs")
        
        if "Arquivo .env não encontrado" in issues:
            recommendations.append("Copie o arquivo .env: cp .env.example .env")
        
        if "Configuração de dispositivos não encontrada" in issues:
            recommendations.append("Crie a configuração: mkdir -p config && nano config/devices.yaml")
        
        # Recomendações de performance
        hardware = self.diagnostic_results.get("hardware", {})
        
        memory = hardware.get("memory", {})
        if memory.get("percent", 0) > 80:
            recommendations.append("Considere aumentar a RAM ou configurar swap")
        
        disk = hardware.get("disk", {})
        if disk.get("percent", 0) > 80:
            recommendations.append("Limpe arquivos desnecessários ou aumente o espaço em disco")
        
        temp = hardware.get("temperature", {})
        if temp.get("cpu", 0) > 70:
            recommendations.append("Verifique a ventilação e considere reduzir a carga de trabalho")
        
        # Recomendações gerais
        recommendations.extend([
            "Execute o script de instalação completo se houver problemas: sudo ./install_ubuntu_raspberry_pi.sh",
            "Configure o arquivo .env com suas credenciais: nano .env",
            "Configure os dispositivos: nano config/devices.yaml",
            "Inicie o sistema: docker-compose up -d",
            "Monitore o sistema: ./monitor.sh"
        ])
        
        return recommendations
    
    def run_diagnostic(self) -> Dict[str, Any]:
        """Executar diagnóstico completo"""
        print("Iniciando diagnóstico do sistema...")
        
        # Executar todas as verificações
        self.diagnostic_results = {
            "system_info": self.check_system_info(),
            "hardware": self.check_hardware(),
            "dependencies": self.check_dependencies(),
            "network": self.check_network(),
            "services": self.check_services(),
            "application": self.check_application(),
            "performance": self.check_performance()
        }
        
        # Analisar problemas
        self.issues = self.analyze_issues()
        
        # Gerar recomendações
        self.recommendations = self.generate_recommendations()
        
        return self.diagnostic_results
    
    def print_report(self):
        """Imprimir relatório de diagnóstico"""
        print("\n" + "="*60)
        print("RELATÓRIO DE DIAGNÓSTICO - RASPBERRY PI UBUNTU")
        print("="*60)
        print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Informações do sistema
        system_info = self.diagnostic_results.get("system_info", {})
        print("SISTEMA:")
        print(f"  Hostname: {system_info.get('hostname', 'N/A')}")
        print(f"  Sistema: {system_info.get('system', 'N/A')}")
        print(f"  Release: {system_info.get('release', 'N/A')}")
        print(f"  Arquitetura: {system_info.get('machine', 'N/A')}")
        print(f"  Python: {system_info.get('python_version', 'N/A')}")
        
        # Hardware
        hardware = self.diagnostic_results.get("hardware", {})
        print(f"\nHARDWARE:")
        print(f"  CPUs: {hardware.get('cpu_count', 'N/A')}")
        
        memory = hardware.get("memory", {})
        if memory:
            print(f"  Memória: {memory.get('total', 0) // (1024**3)} GB total, {memory.get('percent', 0):.1f}% usado")
        
        disk = hardware.get("disk", {})
        if disk:
            print(f"  Disco: {disk.get('total', 0) // (1024**3)} GB total, {disk.get('percent', 0):.1f}% usado")
        
        temp = hardware.get("temperature", {})
        if temp:
            for key, value in temp.items():
                if isinstance(value, (int, float)):
                    print(f"  Temperatura {key.upper()}: {value}°C")
        
        print(f"  GPIO: {'Disponível' if hardware.get('gpio_available', False) else 'Não disponível'}")
        print(f"  Bluetooth: {'Disponível' if hardware.get('bluetooth_available', False) else 'Não disponível'}")
        
        # Dependências
        deps = self.diagnostic_results.get("dependencies", {})
        print(f"\nDEPENDÊNCIAS:")
        
        for dep_name, dep_info in deps.items():
            if isinstance(dep_info, dict) and "available" in dep_info:
                status = "✅" if dep_info["available"] else "❌"
                version = dep_info.get("version", "N/A")
                print(f"  {dep_name}: {status} {version}")
        
        # Rede
        network = self.diagnostic_results.get("network", {})
        print(f"\nREDE:")
        print(f"  Conectividade: {'✅' if network.get('connectivity', False) else '❌'}")
        
        interfaces = network.get("interfaces", [])
        if interfaces:
            print(f"  IPs: {', '.join(interfaces)}")
        
        # Serviços
        services = self.diagnostic_results.get("services", {})
        print(f"\nSERVIÇOS:")
        
        for service, status in services.items():
            if service != "docker_containers":
                status_icon = "✅" if status == "active" else "❌"
                print(f"  {service}: {status_icon} {status}")
        
        # Aplicação
        app = self.diagnostic_results.get("application", {})
        print(f"\nAPLICAÇÃO:")
        print(f"  Diretório: {'✅' if app.get('directory_exists', False) else '❌'}")
        
        files = app.get("files", {})
        for file_name, file_info in files.items():
            status = "✅" if file_info.get("exists", False) else "❌"
            print(f"  {file_name}: {status}")
        
        # Performance
        performance = self.diagnostic_results.get("performance", {})
        print(f"\nPERFORMANCE:")
        print(f"  CPU: {performance.get('cpu_percent', 0):.1f}%")
        print(f"  Memória: {performance.get('memory_percent', 0):.1f}%")
        print(f"  Disco: {performance.get('disk_percent', 0):.1f}%")
        print(f"  Uptime: {performance.get('uptime', 'N/A')}")
        
        # Problemas
        if self.issues:
            print(f"\nPROBLEMAS ENCONTRADOS:")
            for i, issue in enumerate(self.issues, 1):
                print(f"  {i}. {issue}")
        else:
            print(f"\nPROBLEMAS: Nenhum problema encontrado! ✅")
        
        # Recomendações
        if self.recommendations:
            print(f"\nRECOMENDAÇÕES:")
            for i, rec in enumerate(self.recommendations, 1):
                print(f"  {i}. {rec}")
        
        print("="*60)
    
    def save_report(self, filename: str = None):
        """Salvar relatório em arquivo"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"diagnostic_report_{timestamp}.json"
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "diagnostic_results": self.diagnostic_results,
            "issues": self.issues,
            "recommendations": self.recommendations
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"\nRelatório salvo em: {filename}")
        except Exception as e:
            print(f"Erro ao salvar relatório: {e}")

def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Diagnóstico do Sistema de Mineração - Raspberry Pi Ubuntu')
    parser.add_argument('--save', '-s', type=str, 
                       help='Salvar relatório em arquivo JSON')
    parser.add_argument('--quiet', '-q', action='store_true', 
                       help='Modo silencioso (apenas JSON)')
    
    args = parser.parse_args()
    
    # Verificar se está rodando como root
    if os.geteuid() != 0:
        print("❌ Este script deve ser executado como root (sudo)")
        sys.exit(1)
    
    # Executar diagnóstico
    diagnostic = UbuntuRaspberryPiDiagnostic()
    diagnostic.run_diagnostic()
    
    if args.quiet:
        # Modo silencioso - apenas JSON
        report = {
            "timestamp": datetime.now().isoformat(),
            "diagnostic_results": diagnostic.diagnostic_results,
            "issues": diagnostic.issues,
            "recommendations": diagnostic.recommendations
        }
        print(json.dumps(report, indent=2, default=str))
    else:
        # Modo normal - relatório completo
        diagnostic.print_report()
    
    # Salvar relatório se solicitado
    if args.save:
        diagnostic.save_report(args.save)

if __name__ == "__main__":
    main()
