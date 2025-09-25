"""
Sistema de WebSocket para comunicação em tempo real
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Set
from fastapi import WebSocket, WebSocketDisconnect
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class WebSocketMessage:
    """Estrutura de mensagem WebSocket"""
    type: str
    data: Dict[str, Any]
    timestamp: datetime
    target: str = "all"  # all, specific_client, group

class WebSocketManager:
    """Gerenciador de conexões WebSocket"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.connection_groups: Dict[str, Set[WebSocket]] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self.running = False
        
    async def connect(self, websocket: WebSocket):
        """Conectar cliente WebSocket"""
        try:
            await websocket.accept()
            self.active_connections.add(websocket)
            
            logger.info(f"🔌 Cliente WebSocket conectado. Total: {len(self.active_connections)}")
            
            # Enviar mensagem de boas-vindas
            welcome_message = WebSocketMessage(
                type="connection",
                data={
                    "status": "connected",
                    "timestamp": datetime.now().isoformat(),
                    "total_connections": len(self.active_connections)
                },
                timestamp=datetime.now()
            )
            
            await self.send_message_to_client(websocket, welcome_message)
            
            # Manter conexão ativa
            await self._handle_client(websocket)
            
        except WebSocketDisconnect:
            await self.disconnect(websocket)
        except Exception as e:
            logger.error(f"❌ Erro na conexão WebSocket: {e}")
            await self.disconnect(websocket)
    
    async def disconnect(self, websocket: WebSocket):
        """Desconectar cliente WebSocket"""
        try:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
            
            # Remover de grupos
            for group_name, group_connections in self.connection_groups.items():
                if websocket in group_connections:
                    group_connections.remove(websocket)
            
            logger.info(f"🔌 Cliente WebSocket desconectado. Total: {len(self.active_connections)}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao desconectar WebSocket: {e}")
    
    async def _handle_client(self, websocket: WebSocket):
        """Manter conexão com cliente"""
        try:
            while True:
                # Aguardar mensagem do cliente
                data = await websocket.receive_text()
                
                try:
                    message_data = json.loads(data)
                    await self._process_client_message(websocket, message_data)
                except json.JSONDecodeError:
                    logger.warning("⚠️ Mensagem WebSocket inválida recebida")
                except Exception as e:
                    logger.error(f"❌ Erro ao processar mensagem do cliente: {e}")
                    
        except WebSocketDisconnect:
            await self.disconnect(websocket)
        except Exception as e:
            logger.error(f"❌ Erro no handler do cliente: {e}")
            await self.disconnect(websocket)
    
    async def _process_client_message(self, websocket: WebSocket, message_data: Dict[str, Any]):
        """Processar mensagem do cliente"""
        try:
            message_type = message_data.get('type', 'unknown')
            
            if message_type == 'ping':
                # Responder ping com pong
                pong_message = WebSocketMessage(
                    type="pong",
                    data={"timestamp": datetime.now().isoformat()},
                    timestamp=datetime.now()
                )
                await self.send_message_to_client(websocket, pong_message)
            
            elif message_type == 'subscribe':
                # Inscrever em grupo
                group_name = message_data.get('group', 'default')
                await self.add_to_group(websocket, group_name)
            
            elif message_type == 'unsubscribe':
                # Desinscrever de grupo
                group_name = message_data.get('group', 'default')
                await self.remove_from_group(websocket, group_name)
            
            elif message_type == 'request_data':
                # Solicitar dados específicos
                data_type = message_data.get('data_type', 'all')
                await self._send_requested_data(websocket, data_type)
            
            else:
                logger.warning(f"⚠️ Tipo de mensagem desconhecido: {message_type}")
                
        except Exception as e:
            logger.error(f"❌ Erro ao processar mensagem do cliente: {e}")
    
    async def add_to_group(self, websocket: WebSocket, group_name: str):
        """Adicionar cliente a grupo"""
        try:
            if group_name not in self.connection_groups:
                self.connection_groups[group_name] = set()
            
            self.connection_groups[group_name].add(websocket)
            
            logger.info(f"👥 Cliente adicionado ao grupo '{group_name}'. Total no grupo: {len(self.connection_groups[group_name])}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao adicionar cliente ao grupo: {e}")
    
    async def remove_from_group(self, websocket: WebSocket, group_name: str):
        """Remover cliente de grupo"""
        try:
            if group_name in self.connection_groups:
                self.connection_groups[group_name].discard(websocket)
                
                # Remover grupo vazio
                if not self.connection_groups[group_name]:
                    del self.connection_groups[group_name]
            
            logger.info(f"👥 Cliente removido do grupo '{group_name}'")
            
        except Exception as e:
            logger.error(f"❌ Erro ao remover cliente do grupo: {e}")
    
    async def send_message_to_client(self, websocket: WebSocket, message: WebSocketMessage):
        """Enviar mensagem para cliente específico"""
        try:
            message_data = {
                "type": message.type,
                "data": message.data,
                "timestamp": message.timestamp.isoformat()
            }
            
            await websocket.send_text(json.dumps(message_data))
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar mensagem para cliente: {e}")
            await self.disconnect(websocket)
    
    async def broadcast_message(self, message: WebSocketMessage):
        """Transmitir mensagem para todos os clientes"""
        try:
            if not self.active_connections:
                return
            
            message_data = {
                "type": message.type,
                "data": message.data,
                "timestamp": message.timestamp.isoformat()
            }
            
            # Enviar para todos os clientes conectados
            disconnected_clients = set()
            
            for websocket in self.active_connections.copy():
                try:
                    await websocket.send_text(json.dumps(message_data))
                except Exception:
                    disconnected_clients.add(websocket)
            
            # Remover clientes desconectados
            for websocket in disconnected_clients:
                await self.disconnect(websocket)
            
            logger.debug(f"📡 Mensagem transmitida para {len(self.active_connections)} clientes")
            
        except Exception as e:
            logger.error(f"❌ Erro ao transmitir mensagem: {e}")
    
    async def send_message_to_group(self, group_name: str, message: WebSocketMessage):
        """Enviar mensagem para grupo específico"""
        try:
            if group_name not in self.connection_groups:
                logger.warning(f"⚠️ Grupo '{group_name}' não encontrado")
                return
            
            group_connections = self.connection_groups[group_name]
            if not group_connections:
                return
            
            message_data = {
                "type": message.type,
                "data": message.data,
                "timestamp": message.timestamp.isoformat()
            }
            
            # Enviar para todos os clientes do grupo
            disconnected_clients = set()
            
            for websocket in group_connections.copy():
                try:
                    await websocket.send_text(json.dumps(message_data))
                except Exception:
                    disconnected_clients.add(websocket)
            
            # Remover clientes desconectados
            for websocket in disconnected_clients:
                await self.disconnect(websocket)
            
            logger.debug(f"📡 Mensagem enviada para grupo '{group_name}': {len(group_connections)} clientes")
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar mensagem para grupo: {e}")
    
    async def _send_requested_data(self, websocket: WebSocket, data_type: str):
        """Enviar dados solicitados pelo cliente"""
        try:
            if data_type == 'system_status':
                # Enviar status do sistema
                status_message = WebSocketMessage(
                    type="system_status",
                    data={
                        "total_connections": len(self.active_connections),
                        "active_groups": len(self.connection_groups),
                        "timestamp": datetime.now().isoformat()
                    },
                    timestamp=datetime.now()
                )
                await self.send_message_to_client(websocket, status_message)
            
            elif data_type == 'mining_data':
                # Enviar dados de mineração (simulado)
                mining_message = WebSocketMessage(
                    type="mining_data",
                    data={
                        "total_hashrate": 100.5,
                        "active_miners": 9,
                        "total_miners": 10,
                        "efficiency": 0.85,
                        "avg_temperature": 65.0,
                        "timestamp": datetime.now().isoformat()
                    },
                    timestamp=datetime.now()
                )
                await self.send_message_to_client(websocket, mining_message)
            
            else:
                # Enviar dados gerais
                general_message = WebSocketMessage(
                    type="general_data",
                    data={
                        "message": f"Dados solicitados: {data_type}",
                        "timestamp": datetime.now().isoformat()
                    },
                    timestamp=datetime.now()
                )
                await self.send_message_to_client(websocket, general_message)
                
        except Exception as e:
            logger.error(f"❌ Erro ao enviar dados solicitados: {e}")
    
    async def start_message_processor(self):
        """Iniciar processador de mensagens"""
        try:
            self.running = True
            logger.info("📡 Processador de mensagens WebSocket iniciado")
            
            while self.running:
                try:
                    # Processar mensagens da fila
                    if not self.message_queue.empty():
                        message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                        await self._process_queued_message(message)
                    else:
                        await asyncio.sleep(0.1)
                        
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"❌ Erro no processador de mensagens: {e}")
                    await asyncio.sleep(1)
                    
        except Exception as e:
            logger.error(f"❌ Erro no processador de mensagens: {e}")
        finally:
            self.running = False
            logger.info("🛑 Processador de mensagens WebSocket parado")
    
    async def _process_queued_message(self, message: WebSocketMessage):
        """Processar mensagem da fila"""
        try:
            if message.target == "all":
                await self.broadcast_message(message)
            elif message.target in self.connection_groups:
                await self.send_message_to_group(message.target, message)
            else:
                logger.warning(f"⚠️ Target desconhecido: {message.target}")
                
        except Exception as e:
            logger.error(f"❌ Erro ao processar mensagem da fila: {e}")
    
    async def queue_message(self, message: WebSocketMessage):
        """Adicionar mensagem à fila"""
        try:
            await self.message_queue.put(message)
            
        except Exception as e:
            logger.error(f"❌ Erro ao adicionar mensagem à fila: {e}")
    
    async def send_system_alert(self, alert_type: str, message: str, severity: str = "info"):
        """Enviar alerta do sistema"""
        try:
            alert_message = WebSocketMessage(
                type="system_alert",
                data={
                    "alert_type": alert_type,
                    "message": message,
                    "severity": severity,
                    "timestamp": datetime.now().isoformat()
                },
                timestamp=datetime.now(),
                target="all"
            )
            
            await self.queue_message(alert_message)
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar alerta do sistema: {e}")
    
    async def send_mining_update(self, mining_data: Dict[str, Any]):
        """Enviar atualização de mineração"""
        try:
            update_message = WebSocketMessage(
                type="mining_update",
                data=mining_data,
                timestamp=datetime.now(),
                target="all"
            )
            
            await self.queue_message(update_message)
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar atualização de mineração: {e}")
    
    def get_connection_count(self) -> int:
        """Obter número de conexões ativas"""
        return len(self.active_connections)
    
    def get_group_count(self) -> int:
        """Obter número de grupos ativos"""
        return len(self.connection_groups)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Obter estatísticas de conexões"""
        return {
            "total_connections": len(self.active_connections),
            "active_groups": len(self.connection_groups),
            "group_details": {
                name: len(connections) 
                for name, connections in self.connection_groups.items()
            },
            "queue_size": self.message_queue.qsize()
        }
    
    async def shutdown(self):
        """Parar gerenciador WebSocket"""
        try:
            logger.info("🛑 Parando gerenciador WebSocket")
            
            self.running = False
            
            # Desconectar todos os clientes
            for websocket in self.active_connections.copy():
                try:
                    await websocket.close()
                except Exception:
                    pass
            
            self.active_connections.clear()
            self.connection_groups.clear()
            
            logger.info("✅ Gerenciador WebSocket parado")
                
        except Exception as e:
            logger.error(f"❌ Erro ao parar gerenciador WebSocket: {e}")


