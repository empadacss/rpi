#!/usr/bin/env python3
"""
Sistema de Automação para Mineração de Bitcoin
Ponto de entrada principal do sistema
"""

import asyncio
import logging
import signal
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.config import Config
from core.system_manager import SystemManager
from api.routes import router as api_router
from core.websocket import WebSocketManager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bitcoin_mining.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Instância global do sistema
system_manager = None
websocket_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerenciar ciclo de vida da aplicação"""
    global system_manager, websocket_manager
    
    logger.info("🚀 Iniciando Sistema de Automação de Mineração Bitcoin")
    
    try:
        # Carregar configuração
        config = Config()
        
        # Inicializar gerenciador do sistema
        system_manager = SystemManager(config)
        await system_manager.initialize()
        
        # Inicializar WebSocket manager
        websocket_manager = WebSocketManager()
        
        # Iniciar coleta de dados
        await system_manager.start_data_collection()
        
        # Iniciar análise inteligente
        await system_manager.start_intelligent_analysis()
        
        # Iniciar automação
        await system_manager.start_automation()
        
        logger.info("✅ Sistema iniciado com sucesso!")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar sistema: {e}")
        raise
    finally:
        logger.info("🛑 Parando sistema...")
        if system_manager:
            await system_manager.shutdown()
        logger.info("✅ Sistema parado com sucesso!")

# Criar aplicação FastAPI
app = FastAPI(
    title="Bitcoin Mining Automation System",
    description="Sistema completo de automação e monitoramento para mineração de Bitcoin",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rotas da API
app.include_router(api_router, prefix="/api/v1")

# Servir arquivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket):
    await websocket_manager.connect(websocket)

# Health check
@app.get("/health")
async def health_check():
    """Verificar saúde do sistema"""
    if system_manager:
        status = await system_manager.get_status()
        return {
            "status": "healthy",
            "timestamp": status.get("timestamp"),
            "active_collectors": status.get("active_collectors", 0),
            "total_miners": status.get("total_miners", 0),
            "system_uptime": status.get("uptime", 0)
        }
    return {"status": "unhealthy"}

# Endpoint para dados em tempo real
@app.get("/api/v1/realtime")
async def get_realtime_data():
    """Obter dados em tempo real do sistema"""
    if system_manager:
        return await system_manager.get_realtime_data()
    return {"error": "Sistema não inicializado"}

# Endpoint para dashboard
@app.get("/api/v1/dashboard/overview")
async def get_dashboard_overview():
    """Obter visão geral do dashboard"""
    if system_manager:
        return await system_manager.get_dashboard_overview()
    return {"error": "Sistema não inicializado"}

# Endpoint para alertas
@app.get("/api/v1/alerts")
async def get_alerts():
    """Obter alertas ativos"""
    if system_manager:
        return await system_manager.get_active_alerts()
    return {"error": "Sistema não inicializado"}

# Endpoint para controle de ASICs
@app.post("/api/v1/asic/sleep-all")
async def sleep_all_asics():
    """Colocar todos os ASICs em modo sleep"""
    if system_manager:
        result = await system_manager.sleep_all_asics()
        return {"success": True, "result": result}
    return {"error": "Sistema não inicializado"}

@app.post("/api/v1/asic/resume-all")
async def resume_all_asics():
    """Retomar todos os ASICs"""
    if system_manager:
        result = await system_manager.resume_all_asics()
        return {"success": True, "result": result}
    return {"error": "Sistema não inicializado"}

# Endpoint para relatórios
@app.get("/api/v1/reports/financial")
async def get_financial_report():
    """Obter relatório financeiro"""
    if system_manager:
        return await system_manager.get_financial_report()
    return {"error": "Sistema não inicializado"}

@app.get("/api/v1/reports/operational")
async def get_operational_report():
    """Obter relatório operacional"""
    if system_manager:
        return await system_manager.get_operational_report()
    return {"error": "Sistema não inicializado"}

# Configurar handlers de sinal para shutdown graceful
def signal_handler(signum, frame):
    """Handler para sinais do sistema"""
    logger.info(f"Recebido sinal {signum}, iniciando shutdown...")
    if system_manager:
        asyncio.create_task(system_manager.shutdown())
    sys.exit(0)

# Registrar handlers de sinal
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    import uvicorn
    
    # Configurar uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )


