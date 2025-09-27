"""Cliente assíncrono para integração com RabbitMQ."""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

import aio_pika
from aio_pika.abc import AbstractRobustChannel, AbstractRobustConnection

logger = logging.getLogger(__name__)


class RabbitMQClient:
    """Cliente simples para interagir com RabbitMQ usando `aio-pika`."""

    def __init__(self, url: str, *, timeout: float = 5.0) -> None:
        self._url = url
        self._timeout = timeout
        self._connection: Optional[AbstractRobustConnection] = None
        self._channel: Optional[AbstractRobustChannel] = None
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Inicializa a conexão com RabbitMQ."""
        await self.connect()

    async def connect(self) -> None:
        """Abre uma conexão robusta com RabbitMQ."""
        async with self._lock:
            if self._connection and not self._connection.is_closed:
                return

            try:
                self._connection = await aio_pika.connect_robust(
                    self._url,
                    timeout=self._timeout,
                )
                self._channel = await self._connection.channel()
                await self._channel.set_qos(prefetch_count=10)
                logger.info("✅ Conectado ao RabbitMQ em %s", self._url)
            except Exception as exc:  # pragma: no cover - log de infraestrutura
                logger.error("❌ Falha ao conectar no RabbitMQ: %s", exc)
                raise

    async def publish(
        self,
        exchange_name: str,
        routing_key: str,
        payload: bytes,
        *,
        durable_exchange: bool = True,
    ) -> None:
        """Publica uma mensagem em um exchange/topic."""
        await self.connect()

        if not self._channel:
            raise RuntimeError("Canal RabbitMQ não inicializado")

        exchange = await self._channel.declare_exchange(
            exchange_name,
            aio_pika.ExchangeType.TOPIC,
            durable=durable_exchange,
        )
        await exchange.publish(aio_pika.Message(body=payload), routing_key=routing_key)

    async def health_check(self) -> bool:
        """Valida se a conexão está operacional."""
        try:
            await self.connect()
            if not self._channel:
                return False

            # Cria e remove uma fila efêmera para garantir que o canal está funcional
            queue = await self._channel.declare_queue(
                "",
                exclusive=True,
                auto_delete=True,
            )
            await queue.delete()
            return True
        except Exception as exc:  # pragma: no cover - log de infraestrutura
            logger.warning("⚠️ Verificação de saúde do RabbitMQ falhou: %s", exc)
            return False

    async def shutdown(self) -> None:
        """Fecha o canal e a conexão com RabbitMQ."""
        async with self._lock:
            if self._channel:
                await self._channel.close()
                self._channel = None

            if self._connection:
                await self._connection.close()
                self._connection = None
                logger.info("✅ Conexão com RabbitMQ encerrada")

    @property
    def url(self) -> str:
        """Retorna a URL de conexão usada."""
        return self._url
