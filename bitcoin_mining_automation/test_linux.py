#!/usr/bin/env python3
"""
Script de teste específico para Linux
Sistema de Automação para Mineração de Bitcoin
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent))

from backend.core.config import Config
from backend.core.system_manager import SystemManager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_linux.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class LinuxTester:
    """Classe para testar funcionalidades específicas do Linux"""
    
    def __init__(self):
        self.config = None
        self.system_manager = None
        self.test_results = {}
    
    async def initialize(self):
        """Inicializar sistema de teste"""
        try:
            logger.info("Inicializando sistema de teste...")
            
            # Carregar configuração
            self.config = Config()
            
            # Inicializar system manager
            self.system_manager = SystemManager(self.config)
            await self.system_manager.initialize()
            
            logger.info("Sistema de teste inicializado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao inicializar sistema de teste: {e}")
            return False
    
    def test_system_info(self):
        """Testar informações do sistema"""
        logger.info("Testando informações do sistema...")
        
        try:
            import platform
            import psutil
            
            info = {
                "hostname": platform.node(),
                "system": platform.system(),
                "release": platform.release(),
                "architecture": platform.architecture(),
                "python_version": platform.python_version(),
                "cpu_count": psutil.cpu_count(),
                "memory": psutil.virtual_memory()._asdict(),
                "disk": psutil.disk_usage('/')._asdict()
            }
            
            logger.info(f"✅ Sistema: {info['system']} {info['release']}")
            logger.info(f"✅ Arquitetura: {info['architecture']}")
            logger.info(f"✅ Python: {info['python_version']}")
            logger.info(f"✅ CPUs: {info['cpu_count']}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao testar informações do sistema: {e}")
            return False
    
    def test_dependencies(self):
        """Testar dependências"""
        logger.info("Testando dependências...")
        
        try:
            # Testar Python packages
            required_packages = [
                'fastapi', 'uvicorn', 'pydantic', 'sqlalchemy', 
                'psycopg2-binary', 'redis', 'pymodbus', 'requests',
                'httpx', 'schedule', 'tenacity', 'pandas', 'numpy',
                'matplotlib', 'seaborn', 'plotly', 'bleak', 'ttkbootstrap',
                'pillow', 'scikit-learn', 'scipy', 'opencv-python',
                'prometheus-client', 'structlog', 'loguru'
            ]
            
            missing_packages = []
            for package in required_packages:
                try:
                    __import__(package)
                    logger.info(f"✅ {package}")
                except ImportError:
                    missing_packages.append(package)
                    logger.warning(f"❌ {package}")
            
            if missing_packages:
                logger.warning(f"Pacotes faltando: {missing_packages}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao testar dependências: {e}")
            return False
    
    def test_docker(self):
        """Testar Docker"""
        logger.info("Testando Docker...")
        
        try:
            import subprocess
            
            # Verificar Docker
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ Docker: {result.stdout.strip()}")
            else:
                logger.warning("❌ Docker não encontrado")
                return False
            
            # Verificar Docker Compose
            result = subprocess.run(['docker-compose', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ Docker Compose: {result.stdout.strip()}")
            else:
                logger.warning("❌ Docker Compose não encontrado")
                return False
            
            # Verificar se Docker está rodando
            result = subprocess.run(['docker', 'ps'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("✅ Docker está rodando")
            else:
                logger.warning("❌ Docker não está rodando")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao testar Docker: {e}")
            return False
    
    def test_network(self):
        """Testar rede"""
        logger.info("Testando rede...")
        
        try:
            import subprocess
            
            # Testar conectividade
            result = subprocess.run(['ping', '-c', '1', '8.8.8.8'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                logger.info("✅ Conectividade com internet OK")
            else:
                logger.warning("❌ Sem conectividade com internet")
                return False
            
            # Testar portas
            ports = [8000, 3000, 3001, 9090, 15672, 502, 503]
            for port in ports:
                result = subprocess.run(['ss', '-tuln'], 
                                      capture_output=True, text=True)
                if f":{port} " in result.stdout:
                    logger.info(f"✅ Porta {port}: ABERTA")
                else:
                    logger.warning(f"⚠️ Porta {port}: FECHADA")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao testar rede: {e}")
            return False
    
    def test_file_permissions(self):
        """Testar permissões de arquivos"""
        logger.info("Testando permissões de arquivos...")
        
        try:
            base_path = Path("/opt/bitcoin_mining")
            
            # Verificar se diretório existe
            if not base_path.exists():
                logger.error("❌ Diretório /opt/bitcoin_mining não existe")
                return False
            
            # Verificar permissões
            if os.access(base_path, os.R_OK):
                logger.info("✅ Diretório legível")
            else:
                logger.error("❌ Diretório não legível")
                return False
            
            if os.access(base_path, os.W_OK):
                logger.info("✅ Diretório gravável")
            else:
                logger.error("❌ Diretório não gravável")
                return False
            
            if os.access(base_path, os.X_OK):
                logger.info("✅ Diretório executável")
            else:
                logger.error("❌ Diretório não executável")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao testar permissões: {e}")
            return False
    
    def test_configuration_files(self):
        """Testar arquivos de configuração"""
        logger.info("Testando arquivos de configuração...")
        
        try:
            base_path = Path("/opt/bitcoin_mining")
            
            # Arquivos importantes
            important_files = [
                "main.py",
                "docker-compose.yml",
                "requirements.txt",
                ".env",
                "config/devices.yaml"
            ]
            
            missing_files = []
            for file_path in important_files:
                full_path = base_path / file_path
                if full_path.exists():
                    logger.info(f"✅ {file_path}")
                else:
                    missing_files.append(file_path)
                    logger.warning(f"❌ {file_path}")
            
            if missing_files:
                logger.warning(f"Arquivos faltando: {missing_files}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao testar arquivos de configuração: {e}")
            return False
    
    def test_services(self):
        """Testar serviços"""
        logger.info("Testando serviços...")
        
        try:
            import subprocess
            
            # Serviços systemd
            services = [
                'bitcoin-mining.service',
                'bitcoin-mining-python.service',
                'docker.service'
            ]
            
            for service in services:
                result = subprocess.run(['systemctl', 'is-active', service], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    status = result.stdout.strip()
                    if status == 'active':
                        logger.info(f"✅ {service}: {status}")
                    else:
                        logger.warning(f"⚠️ {service}: {status}")
                else:
                    logger.warning(f"❌ {service}: não encontrado")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao testar serviços: {e}")
            return False
    
    def test_application_components(self):
        """Testar componentes da aplicação"""
        logger.info("Testando componentes da aplicação...")
        
        try:
            if not self.system_manager:
                logger.error("❌ System manager não inicializado")
                return False
            
            # Testar coletores
            collectors = self.system_manager.collectors
            if collectors:
                logger.info(f"✅ {len(collectors)} coletores encontrados")
                for name, collector in collectors.items():
                    logger.info(f"  - {name}: {type(collector).__name__}")
            else:
                logger.warning("⚠️ Nenhum coletor encontrado")
            
            # Testar gerenciadores
            managers = self.system_manager.managers
            if managers:
                logger.info(f"✅ {len(managers)} gerenciadores encontrados")
                for name, manager in managers.items():
                    logger.info(f"  - {name}: {type(manager).__name__}")
            else:
                logger.warning("⚠️ Nenhum gerenciador encontrado")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao testar componentes da aplicação: {e}")
            return False
    
    def test_logs(self):
        """Testar logs"""
        logger.info("Testando logs...")
        
        try:
            logs_path = Path("/opt/bitcoin_mining/logs")
            if not logs_path.exists():
                logger.warning("⚠️ Diretório de logs não existe")
                return False
            
            log_files = list(logs_path.glob("*.log"))
            if log_files:
                logger.info(f"✅ {len(log_files)} arquivos de log encontrados")
                for log_file in log_files:
                    size = log_file.stat().st_size
                    logger.info(f"  - {log_file.name}: {size} bytes")
            else:
                logger.warning("⚠️ Nenhum arquivo de log encontrado")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao testar logs: {e}")
            return False
    
    async def run_all_tests(self):
        """Executar todos os testes"""
        logger.info("Iniciando bateria de testes...")
        
        tests = [
            ("System Info", self.test_system_info),
            ("Dependencies", self.test_dependencies),
            ("Docker", self.test_docker),
            ("Network", self.test_network),
            ("File Permissions", self.test_file_permissions),
            ("Configuration Files", self.test_configuration_files),
            ("Services", self.test_services),
            ("Application Components", self.test_application_components),
            ("Logs", self.test_logs),
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            try:
                logger.info(f"Executando teste: {test_name}")
                result = test_func()
                results[test_name] = result
                
                if result:
                    logger.info(f"✅ {test_name}: PASSOU")
                else:
                    logger.warning(f"❌ {test_name}: FALHOU")
                    
            except Exception as e:
                logger.error(f"❌ {test_name}: ERRO - {e}")
                results[test_name] = False
        
        return results
    
    def generate_report(self, results):
        """Gerar relatório de testes"""
        logger.info("Gerando relatório de testes...")
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        success_rate = (passed / total) * 100
        
        report = f"""
==========================================
RELATÓRIO DE TESTES - LINUX
==========================================
Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total de testes: {total}
Testes aprovados: {passed}
Taxa de sucesso: {success_rate:.1f}%

==========================================
RESULTADOS DETALHADOS
==========================================
"""
        
        for test_name, result in results.items():
            status = "✅ PASSOU" if result else "❌ FALHOU"
            report += f"{test_name:<25}: {status}\n"
        
        report += f"""
==========================================
RECOMENDAÇÕES
==========================================
"""
        
        if not results.get("Dependencies", False):
            report += "- Instale as dependências Python faltantes\n"
        
        if not results.get("Docker", False):
            report += "- Instale e configure o Docker\n"
        
        if not results.get("Network", False):
            report += "- Verifique a conectividade de rede\n"
        
        if not results.get("File Permissions", False):
            report += "- Verifique as permissões dos arquivos\n"
        
        if not results.get("Configuration Files", False):
            report += "- Crie os arquivos de configuração faltantes\n"
        
        if not results.get("Services", False):
            report += "- Configure e inicie os serviços do sistema\n"
        
        if not results.get("Application Components", False):
            report += "- Verifique a inicialização da aplicação\n"
        
        if not results.get("Logs", False):
            report += "- Verifique a configuração de logs\n"
        
        report += f"""
==========================================
PRÓXIMOS PASSOS
==========================================
1. Corrija os problemas identificados
2. Execute novamente: python test_linux.py
3. Inicie o sistema: docker-compose up -d
4. Acesse: http://localhost:8000
5. Monitore: ./monitor.sh

==========================================
"""
        
        return report

async def main():
    """Função principal"""
    logger.info("Iniciando testes do sistema no Linux...")
    
    # Criar diretório de logs se não existir
    os.makedirs("logs", exist_ok=True)
    
    # Inicializar tester
    tester = LinuxTester()
    
    # Inicializar sistema
    if not await tester.initialize():
        logger.error("Falha ao inicializar sistema de teste")
        return
    
    # Executar testes
    results = await tester.run_all_tests()
    
    # Gerar relatório
    report = tester.generate_report(results)
    
    # Salvar relatório
    with open("logs/test_report.txt", "w") as f:
        f.write(report)
    
    # Exibir relatório
    print(report)
    
    # Salvar relatório no console
    logger.info("Relatório salvo em: logs/test_report.txt")
    
    # Fechar sistema
    if tester.system_manager:
        await tester.system_manager.shutdown()

if __name__ == "__main__":
    asyncio.run(main())

