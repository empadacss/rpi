"""
Sistema de notificações para mineração de Bitcoin
"""

import asyncio
import logging
import smtplib
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import httpx
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class NotificationChannel(Enum):
    """Canais de notificação"""
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    SMS = "sms"
    WEBHOOK = "webhook"

class AlertSeverity(Enum):
    """Severidade do alerta"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class Alert:
    """Estrutura de alerta"""
    id: str
    type: str
    severity: AlertSeverity
    message: str
    timestamp: datetime
    data: Dict[str, Any]
    channels: List[NotificationChannel]
    sent: bool = False
    retry_count: int = 0

class NotificationManager:
    """Gerenciador de notificações"""
    
    def __init__(self, config):
        self.config = config
        self.running = False
        self.alerts = []
        self.notification_config = config.get_notification_config()
        self.max_alerts = 1000
        self.retry_attempts = 3
        self.retry_delay = 60  # segundos
        
        # Inicializar clientes de notificação
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Inicializar clientes de notificação"""
        try:
            # Cliente de email
            self.email_client = EmailClient(self.notification_config.get('smtp', {}))
            
            # Cliente WhatsApp
            self.whatsapp_client = WhatsAppClient(self.notification_config.get('whatsapp_token'))
            
            # Cliente Telegram
            self.telegram_client = TelegramClient(self.notification_config.get('telegram_bot_token'))
            
            # Cliente SMS
            self.sms_client = SMSClient()
            
            logger.info("✅ Clientes de notificação inicializados")
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar clientes de notificação: {e}")
    
    async def initialize(self):
        """Inicializar gerenciador"""
        try:
            logger.info("📢 Inicializando gerenciador de notificações")
            self.running = True
            logger.info("✅ Gerenciador de notificações inicializado com sucesso")

        except Exception as e:
            logger.error(f"❌ Erro ao inicializar gerenciador: {e}")
            raise
    
    async def send_alert(self, alert_type: str, message: str, severity: str = "info", 
                        data: Optional[Dict[str, Any]] = None, 
                        channels: Optional[List[str]] = None):
        """Enviar alerta"""
        try:
            # Criar alerta
            alert = Alert(
                id=f"{alert_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                type=alert_type,
                severity=AlertSeverity(severity),
                message=message,
                timestamp=datetime.now(),
                data=data or {},
                channels=[NotificationChannel(c) for c in (channels or ['email'])]
            )
            
            # Adicionar à lista de alertas
            self.alerts.append(alert)
            
            # Manter apenas os últimos N alertas
            if len(self.alerts) > self.max_alerts:
                self.alerts = self.alerts[-self.max_alerts:]
            
            # Enviar notificação
            await self._send_notification(alert)
            
            logger.info(f"📢 Alerta enviado: {alert_type} - {message}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar alerta: {e}")
    
    async def _send_notification(self, alert: Alert):
        """Enviar notificação para os canais especificados"""
        try:
            for channel in alert.channels:
                try:
                    if channel == NotificationChannel.EMAIL:
                        await self._send_email(alert)
                    
                    elif channel == NotificationChannel.WHATSAPP:
                        await self._send_whatsapp(alert)
                    
                    elif channel == NotificationChannel.TELEGRAM:
                        await self._send_telegram(alert)
                    
                    elif channel == NotificationChannel.SMS:
                        await self._send_sms(alert)
                    
                    elif channel == NotificationChannel.WEBHOOK:
                        await self._send_webhook(alert)
                    
                    logger.debug(f"✅ Notificação enviada via {channel.value}")
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao enviar via {channel.value}: {e}")
                    alert.retry_count += 1
            
            # Marcar como enviado se pelo menos um canal funcionou
            if alert.retry_count < len(alert.channels):
                alert.sent = True
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar notificação: {e}")
    
    async def _send_email(self, alert: Alert):
        """Enviar email"""
        try:
            await self.email_client.send_alert(alert)
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar email: {e}")
            raise
    
    async def _send_whatsapp(self, alert: Alert):
        """Enviar WhatsApp"""
        try:
            await self.whatsapp_client.send_alert(alert)
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar WhatsApp: {e}")
            raise
    
    async def _send_telegram(self, alert: Alert):
        """Enviar Telegram"""
        try:
            await self.telegram_client.send_alert(alert)
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar Telegram: {e}")
            raise
    
    async def _send_sms(self, alert: Alert):
        """Enviar SMS"""
        try:
            await self.sms_client.send_alert(alert)
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar SMS: {e}")
            raise
    
    async def _send_webhook(self, alert: Alert):
        """Enviar webhook"""
        try:
            # Implementar webhook
            logger.info(f"🔗 Webhook enviado: {alert.message}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar webhook: {e}")
            raise
    
    async def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Obter alertas ativos"""
        try:
            # Filtrar alertas das últimas 24 horas
            cutoff_time = datetime.now() - timedelta(hours=24)
            
            active_alerts = [
                {
                    'id': alert.id,
                    'type': alert.type,
                    'severity': alert.severity.value,
                    'message': alert.message,
                    'timestamp': alert.timestamp.isoformat(),
                    'data': alert.data,
                    'channels': [c.value for c in alert.channels],
                    'sent': alert.sent,
                    'retry_count': alert.retry_count
                }
                for alert in self.alerts
                if alert.timestamp > cutoff_time
            ]
            
            return active_alerts
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter alertas ativos: {e}")
            return []
    
    async def get_active_alerts_count(self) -> int:
        """Obter contagem de alertas ativos"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=24)
            return len([a for a in self.alerts if a.timestamp > cutoff_time])
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter contagem de alertas: {e}")
            return 0
    
    async def clear_old_alerts(self, days: int = 7):
        """Limpar alertas antigos"""
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            self.alerts = [a for a in self.alerts if a.timestamp > cutoff_time]
            
            logger.info(f"✅ Alertas antigos removidos (mais de {days} dias)")
            
        except Exception as e:
            logger.error(f"❌ Erro ao limpar alertas antigos: {e}")
    
    def is_active(self) -> bool:
        """Verificar se o gerenciador está ativo"""
        return self.running
    
    async def shutdown(self):
        """Parar gerenciador"""
        try:
            logger.info("🛑 Parando gerenciador de notificações")
            self.running = False
            logger.info("✅ Gerenciador de notificações parado")
                
        except Exception as e:
            logger.error(f"❌ Erro ao parar gerenciador: {e}")

class EmailClient:
    """Cliente de email"""
    
    def __init__(self, config):
        self.config = config
        self.smtp_host = config.get('host', 'smtp.gmail.com')
        self.smtp_port = config.get('port', 587)
        self.username = config.get('user')
        self.password = config.get('password')
        self.from_email = config.get('user')
    
    async def send_alert(self, alert: Alert):
        """Enviar alerta por email"""
        try:
            if not self.username or not self.password:
                logger.warning("⚠️ Credenciais de email não configuradas")
                return
            
            # Criar mensagem
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = self.from_email  # Em produção, usar lista de destinatários
            msg['Subject'] = f"🚨 Alerta de Mineração: {alert.type}"
            
            # Corpo do email
            body = f"""
            <h2>Alerta de Mineração de Bitcoin</h2>
            <p><strong>Tipo:</strong> {alert.type}</p>
            <p><strong>Severidade:</strong> {alert.severity.value.upper()}</p>
            <p><strong>Mensagem:</strong> {alert.message}</p>
            <p><strong>Timestamp:</strong> {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <h3>Dados Adicionais:</h3>
            <pre>{json.dumps(alert.data, indent=2)}</pre>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            # Enviar email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            logger.info("✅ Email enviado com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar email: {e}")
            raise

class WhatsAppClient:
    """Cliente WhatsApp"""
    
    def __init__(self, token: Optional[str]):
        self.token = token
        self.base_url = "https://graph.facebook.com/v17.0"
    
    async def send_alert(self, alert: Alert):
        """Enviar alerta por WhatsApp"""
        try:
            if not self.token:
                logger.warning("⚠️ Token do WhatsApp não configurado")
                return
            
            # Implementar envio via API do WhatsApp Business
            message = f"🚨 *Alerta de Mineração*\n\n"
            message += f"*Tipo:* {alert.type}\n"
            message += f"*Severidade:* {alert.severity.value.upper()}\n"
            message += f"*Mensagem:* {alert.message}\n"
            message += f"*Timestamp:* {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            if alert.data:
                message += f"\n*Dados:*\n{json.dumps(alert.data, indent=2)}"
            
            # Em produção, implementar envio real via API
            logger.info(f"📱 WhatsApp: {message}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar WhatsApp: {e}")
            raise

class TelegramClient:
    """Cliente Telegram"""
    
    def __init__(self, token: Optional[str]):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}" if token else None
    
    async def send_alert(self, alert: Alert):
        """Enviar alerta por Telegram"""
        try:
            if not self.token:
                logger.warning("⚠️ Token do Telegram não configurado")
                return
            
            message = f"🚨 *Alerta de Mineração*\n\n"
            message += f"*Tipo:* {alert.type}\n"
            message += f"*Severidade:* {alert.severity.value.upper()}\n"
            message += f"*Mensagem:* {alert.message}\n"
            message += f"*Timestamp:* {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            if alert.data:
                message += f"\n*Dados:*\n```json\n{json.dumps(alert.data, indent=2)}\n```"
            
            # Em produção, implementar envio real via API
            logger.info(f"📱 Telegram: {message}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar Telegram: {e}")
            raise

class SMSClient:
    """Cliente SMS"""
    
    def __init__(self):
        pass
    
    async def send_alert(self, alert: Alert):
        """Enviar alerta por SMS"""
        try:
            message = f"ALERTA MINERACAO: {alert.type} - {alert.message}"
            
            # Em produção, implementar envio real via API de SMS
            logger.info(f"📱 SMS: {message}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar SMS: {e}")
            raise


