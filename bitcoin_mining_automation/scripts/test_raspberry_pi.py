#!/usr/bin/env python3
"""
Script de teste específico para Raspberry Pi
Sistema de Automação para Mineração de Bitcoin
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from backend.core.config import Config
from backend.core.system_manager import SystemManager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_raspberry_pi.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class RaspberryPiTester:
    """Classe para testar funcionalidades específicas do Raspberry Pi"""
    
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
    
    async def test_gpio_access(self):
        """Testar acesso ao GPIO"""
        logger.info("Testando acesso ao GPIO...")
        
        try:
            # Verificar se GPIO está disponível
            gpio_path = Path("/sys/class/gpio")
            if not gpio_path.exists():
                logger.warning("GPIO não disponível - funcionalidades de controle limitadas")
                return False
            
            # Verificar permissões
            if not os.access("/sys/class/gpio", os.R_OK):
                logger.warning("Sem permissão de leitura no GPIO")
                return False
            
            logger.info("✅ GPIO acessível")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao testar GPIO: {e}")
            return False
    
    async def test_bluetooth(self):
        """Testar funcionalidade Bluetooth"""
        logger.info("Testando Bluetooth...")
        
        try:
            # Verificar se bluetoothctl está disponível
            import subprocess
            result = subprocess.run(['bluetoothctl', '--version'], 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.warning("bluetoothctl não disponível")
                return False
            
            # Verificar se Bluetooth está ativo
            result = subprocess.run(['bluetoothctl', 'show'], 
                                  capture_output=True, text=True)
            
            if "Powered: yes" in result.stdout:
                logger.info("✅ Bluetooth ativo")
                return True
            else:
                logger.warning("Bluetooth inativo")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao testar Bluetooth: {e}")
            return False
    
    async def test_modbus_connection(self):
        """Testar conexão Modbus"""
        logger.info("Testando conexão Modbus...")
        
        try:
            from backend.core.data_collectors.abb_collector import ABBCollector
            
            collector = ABBCollector(self.config)
            await collector.initialize()
            
            # Testar conexão com inversor
            inverter_data = await collector.read_inverter_data()
            if inverter_data:
                logger.info("✅ Conexão Modbus com inversor OK")
                return True
            else:
                logger.warning("Falha na conexão Modbus com inversor")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao testar Modbus: {e}")
            return False
    
    async def test_ble_sensors(self):
        """Testar sensores BLE"""
        logger.info("Testando sensores BLE...")
        
        try:
            from backend.core.data_collectors.ble_collector import BLECollector
            
            collector = BLECollector(self.config)
            await collector.initialize()
            
            # Testar descoberta de sensores
            sensors = await collector.discover_sensors()
            if sensors:
                logger.info(f"✅ {len(sensors)} sensores BLE encontrados")
                return True
            else:
                logger.warning("Nenhum sensor BLE encontrado")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao testar sensores BLE: {e}")
            return False
    
    async def test_asic_control(self):
        """Testar controle de ASICs"""
        logger.info("Testando controle de ASICs...")
        
        try:
            from backend.core.data_collectors.asic_collector import ASICCollector
            
            collector = ASICCollector(self.config)
            await collector.initialize()
            
            # Testar descoberta de ASICs
            asics = await collector.discover_asics()
            if asics:
                logger.info(f"✅ {len(asics)} ASICs encontrados")
                return True
            else:
                logger.warning("Nenhum ASIC encontrado")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao testar ASICs: {e}")
            return False
    
    async def test_pool_connection(self):
        """Testar conexão com pool"""
        logger.info("Testando conexão com pool...")
        
        try:
            from backend.core.data_collectors.pool_collector import PoolCollector
            
            collector = PoolCollector(self.config)
            await collector.initialize()
            
            # Testar conexão com F2Pool
            pool_data = await collector.get_pool_data()
            if pool_data:
                logger.info("✅ Conexão com F2Pool OK")
                return True
            else:
                logger.warning("Falha na conexão com F2Pool")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao testar pool: {e}")
            return False
    
    async def test_database_connection(self):
        """Testar conexão com banco de dados"""
        logger.info("Testando conexão com banco de dados...")
        
        try:
            from backend.core.persistence.database import DatabaseManager
            
            db_manager = DatabaseManager(self.config)
            await db_manager.initialize()
            
            # Testar conexão
            if db_manager.engine:
                logger.info("✅ Conexão com banco de dados OK")
                return True
            else:
                logger.warning("Falha na conexão com banco de dados")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao testar banco de dados: {e}")
            return False
    
    async def test_llm_connection(self):
        """Testar conexão com LLM"""
        logger.info("Testando conexão com LLM...")
        
        try:
            from backend.core.analytics.intelligent_analyzer import IntelligentAnalyzer
            
            analyzer = IntelligentAnalyzer(self.config)
            await analyzer.initialize()
            
            # Testar conexão
            if analyzer.llm_client:
                logger.info("✅ Conexão com LLM OK")
                return True
            else:
                logger.warning("Falha na conexão com LLM")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao testar LLM: {e}")
            return False
    
    async def test_automation_system(self):
        """Testar sistema de automação"""
        logger.info("Testando sistema de automação...")
        
        try:
            from backend.core.automation.automation_controller import AutomationController
            
            controller = AutomationController(self.config)
            await controller.initialize()
            
            # Testar inicialização
            if controller:
                logger.info("✅ Sistema de automação OK")
                return True
            else:
                logger.warning("Falha no sistema de automação")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao testar automação: {e}")
            return False
    
    async def test_safety_controller(self):
        """Testar controlador de segurança"""
        logger.info("Testando controlador de segurança...")
        
        try:
            from backend.core.automation.safety_controller import SafetyController
            
            controller = SafetyController(self.config)
            await controller.initialize()
            
            # Testar inicialização
            if controller:
                logger.info("✅ Controlador de segurança OK")
                return True
            else:
                logger.warning("Falha no controlador de segurança")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao testar controlador de segurança: {e}")
            return False
    
    async def test_scheduler(self):
        """Testar agendador"""
        logger.info("Testando agendador...")
        
        try:
            from backend.core.automation.scheduler import Scheduler
            
            scheduler = Scheduler(self.config)
            await scheduler.initialize()
            
            # Testar inicialização
            if scheduler:
                logger.info("✅ Agendador OK")
                return True
            else:
                logger.warning("Falha no agendador")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao testar agendador: {e}")
            return False
    
    async def test_report_generator(self):
        """Testar gerador de relatórios"""
        logger.info("Testando gerador de relatórios...")
        
        try:
            from backend.core.persistence.report_generator import ReportGenerator
            
            generator = ReportGenerator(self.config)
            await generator.initialize()
            
            # Testar inicialização
            if generator:
                logger.info("✅ Gerador de relatórios OK")
                return True
            else:
                logger.warning("Falha no gerador de relatórios")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao testar gerador de relatórios: {e}")
            return False
    
    async def test_notification_system(self):
        """Testar sistema de notificações"""
        logger.info("Testando sistema de notificações...")
        
        try:
            from backend.core.notifications.notification_manager import NotificationManager
            
            manager = NotificationManager(self.config)
            await manager.initialize()
            
            # Testar inicialização
            if manager:
                logger.info("✅ Sistema de notificações OK")
                return True
            else:
                logger.warning("Falha no sistema de notificações")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao testar notificações: {e}")
            return False
    
    async def test_websocket_system(self):
        """Testar sistema WebSocket"""
        logger.info("Testando sistema WebSocket...")
        
        try:
            from backend.core.websocket import WebSocketManager
            
            manager = WebSocketManager(self.config)
            await manager.initialize()
            
            # Testar inicialização
            if manager:
                logger.info("✅ Sistema WebSocket OK")
                return True
            else:
                logger.warning("Falha no sistema WebSocket")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao testar WebSocket: {e}")
            return False
    
    async def test_gui_interface(self):
        """Testar interface gráfica"""
        logger.info("Testando interface gráfica...")
        
        try:
            import tkinter as tk
            from tkinter import ttk
            
            # Testar criação de janela básica
            root = tk.Tk()
            root.withdraw()  # Esconder janela
            
            # Testar ttkbootstrap
            try:
                import ttkbootstrap as ttk
                style = ttk.Style()
                logger.info("✅ Interface gráfica OK (ttkbootstrap disponível)")
                return True
            except ImportError:
                logger.warning("ttkbootstrap não disponível - usando tkinter padrão")
                return True
                
        except Exception as e:
            logger.error(f"Erro ao testar interface gráfica: {e}")
            return False
    
    async def run_all_tests(self):
        """Executar todos os testes"""
        logger.info("Iniciando bateria de testes...")
        
        tests = [
            ("GPIO", self.test_gpio_access),
            ("Bluetooth", self.test_bluetooth),
            ("Modbus", self.test_modbus_connection),
            ("BLE Sensors", self.test_ble_sensors),
            ("ASIC Control", self.test_asic_control),
            ("Pool Connection", self.test_pool_connection),
            ("Database", self.test_database_connection),
            ("LLM", self.test_llm_connection),
            ("Automation", self.test_automation_system),
            ("Safety Controller", self.test_safety_controller),
            ("Scheduler", self.test_scheduler),
            ("Report Generator", self.test_report_generator),
            ("Notifications", self.test_notification_system),
            ("WebSocket", self.test_websocket_system),
            ("GUI Interface", self.test_gui_interface),
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            try:
                logger.info(f"Executando teste: {test_name}")
                result = await test_func()
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
RELATÓRIO DE TESTES - RASPBERRY PI
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
            report += f"{test_name:<20}: {status}\n"
        
        report += f"""
==========================================
RECOMENDAÇÕES
==========================================
"""
        
        if not results.get("GPIO", False):
            report += "- Configure permissões de GPIO para controle de ventiladores\n"
        
        if not results.get("Bluetooth", False):
            report += "- Ative o Bluetooth para sensores BLE\n"
        
        if not results.get("Modbus", False):
            report += "- Verifique conectividade de rede com dispositivos Modbus\n"
        
        if not results.get("BLE Sensors", False):
            report += "- Verifique se os sensores BLE estão próximos e pareados\n"
        
        if not results.get("ASIC Control", False):
            report += "- Instale o HashCore Toolkit e verifique conectividade com ASICs\n"
        
        if not results.get("Pool Connection", False):
            report += "- Configure tokens de API da F2Pool\n"
        
        if not results.get("Database", False):
            report += "- Verifique configuração do banco de dados\n"
        
        if not results.get("LLM", False):
            report += "- Configure endpoint da LLM (local ou remoto)\n"
        
        if not results.get("GUI Interface", False):
            report += "- Instale dependências da interface gráfica\n"
        
        report += f"""
==========================================
PRÓXIMOS PASSOS
==========================================
1. Corrija os problemas identificados
2. Execute novamente: python test_raspberry_pi.py
3. Inicie o sistema: docker-compose up -d
4. Acesse: http://localhost:8000
5. Monitore: ./monitor.sh

==========================================
"""
        
        return report

async def main():
    """Função principal"""
    logger.info("Iniciando testes do sistema no Raspberry Pi...")
    
    # Criar diretório de logs se não existir
    os.makedirs("logs", exist_ok=True)
    
    # Inicializar tester
    tester = RaspberryPiTester()
    
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


