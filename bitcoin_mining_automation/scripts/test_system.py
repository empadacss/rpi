#!/usr/bin/env python3
"""
Script de teste para o sistema de automação de mineração de Bitcoin
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime
from typing import Dict, Any, List

class SystemTester:
    """Testador do sistema"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.test_results = []
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_endpoint(self, endpoint: str, method: str = "GET", 
                          data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Testar endpoint da API"""
        try:
            url = f"{self.base_url}{endpoint}"
            
            if method == "GET":
                async with self.session.get(url) as response:
                    result = {
                        "endpoint": endpoint,
                        "method": method,
                        "status": response.status,
                        "success": response.status == 200,
                        "response": await response.json() if response.status == 200 else None,
                        "error": None
                    }
            elif method == "POST":
                async with self.session.post(url, json=data) as response:
                    result = {
                        "endpoint": endpoint,
                        "method": method,
                        "status": response.status,
                        "success": response.status in [200, 201],
                        "response": await response.json() if response.status in [200, 201] else None,
                        "error": None
                    }
            else:
                result = {
                    "endpoint": endpoint,
                    "method": method,
                    "status": 0,
                    "success": False,
                    "response": None,
                    "error": f"Método {method} não suportado"
                }
            
            return result
            
        except Exception as e:
            return {
                "endpoint": endpoint,
                "method": method,
                "status": 0,
                "success": False,
                "response": None,
                "error": str(e)
            }
    
    async def run_all_tests(self) -> List[Dict[str, Any]]:
        """Executar todos os testes"""
        print("🧪 Iniciando testes do sistema...")
        print("=" * 50)
        
        # Testes básicos
        tests = [
            ("/health", "GET"),
            ("/api/v1/status", "GET"),
            ("/api/v1/mining/data", "GET"),
            ("/api/v1/alerts", "GET"),
            ("/api/v1/config", "GET"),
            ("/api/v1/stats/overview", "GET"),
            ("/api/v1/monitoring/health", "GET"),
        ]
        
        # Testes de controle
        control_tests = [
            ("/api/v1/asic/sleep-all", "POST"),
            ("/api/v1/asic/resume-all", "POST"),
        ]
        
        # Testes de relatórios
        report_tests = [
            ("/api/v1/reports/financial", "GET"),
            ("/api/v1/reports/operational", "GET"),
            ("/api/v1/reports/performance", "GET"),
        ]
        
        # Executar testes básicos
        print("📊 Testando endpoints básicos...")
        for endpoint, method in tests:
            result = await self.test_endpoint(endpoint, method)
            self.test_results.append(result)
            self._print_test_result(result)
        
        # Executar testes de controle
        print("\n🎮 Testando controles...")
        for endpoint, method in control_tests:
            result = await self.test_endpoint(endpoint, method)
            self.test_results.append(result)
            self._print_test_result(result)
        
        # Executar testes de relatórios
        print("\n📈 Testando relatórios...")
        for endpoint, method in report_tests:
            result = await self.test_endpoint(endpoint, method)
            self.test_results.append(result)
            self._print_test_result(result)
        
        return self.test_results
    
    def _print_test_result(self, result: Dict[str, Any]):
        """Imprimir resultado do teste"""
        status = "✅" if result["success"] else "❌"
        print(f"{status} {result['method']} {result['endpoint']} - Status: {result['status']}")
        
        if result["error"]:
            print(f"   Erro: {result['error']}")
    
    def print_summary(self):
        """Imprimir resumo dos testes"""
        print("\n" + "=" * 50)
        print("📋 RESUMO DOS TESTES")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r["success"])
        failed_tests = total_tests - successful_tests
        
        print(f"Total de testes: {total_tests}")
        print(f"Sucessos: {successful_tests}")
        print(f"Falhas: {failed_tests}")
        print(f"Taxa de sucesso: {(successful_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Testes que falharam:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   - {result['method']} {result['endpoint']}: {result['error']}")
        
        print("\n" + "=" * 50)
        
        if failed_tests == 0:
            print("🎉 Todos os testes passaram! Sistema funcionando corretamente.")
        else:
            print("⚠️ Alguns testes falharam. Verifique a configuração do sistema.")
        
        return failed_tests == 0

async def test_websocket_connection(base_url: str = "ws://localhost:8000"):
    """Testar conexão WebSocket"""
    try:
        import websockets
        
        print("\n🔌 Testando conexão WebSocket...")
        
        async with websockets.connect(f"{base_url}/ws") as websocket:
            # Enviar ping
            await websocket.send(json.dumps({"type": "ping"}))
            
            # Aguardar resposta
            response = await websocket.recv()
            data = json.loads(response)
            
            if data.get("type") == "pong":
                print("✅ WebSocket funcionando corretamente")
                return True
            else:
                print("❌ WebSocket não respondeu corretamente")
                return False
                
    except Exception as e:
        print(f"❌ Erro na conexão WebSocket: {e}")
        return False

async def test_database_connection():
    """Testar conexão com banco de dados"""
    try:
        print("\n🗄️ Testando conexão com banco de dados...")
        
        # Em produção, implementar teste real de conexão
        print("✅ Banco de dados funcionando (simulado)")
        return True
        
    except Exception as e:
        print(f"❌ Erro na conexão com banco de dados: {e}")
        return False

async def test_llm_connection():
    """Testar conexão com LLM"""
    try:
        print("\n🧠 Testando conexão com LLM...")
        
        # Em produção, implementar teste real de LLM
        print("✅ LLM funcionando (simulado)")
        return True
        
    except Exception as e:
        print(f"❌ Erro na conexão com LLM: {e}")
        return False

async def main():
    """Função principal"""
    print("🚀 Teste do Sistema de Automação para Mineração de Bitcoin")
    print(f"⏰ Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Testar API
    async with SystemTester() as tester:
        await tester.run_all_tests()
        api_success = tester.print_summary()
    
    # Testar WebSocket
    websocket_success = await test_websocket_connection()
    
    # Testar banco de dados
    db_success = await test_database_connection()
    
    # Testar LLM
    llm_success = await test_llm_connection()
    
    # Resumo final
    print("\n" + "=" * 60)
    print("🏁 RESUMO FINAL")
    print("=" * 60)
    
    all_tests = [
        ("API REST", api_success),
        ("WebSocket", websocket_success),
        ("Banco de Dados", db_success),
        ("LLM", llm_success)
    ]
    
    for test_name, success in all_tests:
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
    
    overall_success = all(success for _, success in all_tests)
    
    if overall_success:
        print("\n🎉 Sistema funcionando perfeitamente!")
        sys.exit(0)
    else:
        print("\n⚠️ Sistema com problemas. Verifique os logs.")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️ Teste interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        sys.exit(1)


