"""SQLite persistence layer."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Dict, Iterable, Iterator, Optional

from .config import DatabaseConfig


@dataclass
class Database:
    cfg: DatabaseConfig

    def initialise(self) -> None:
        self.cfg.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS inverter_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    frequency REAL,
                    current REAL,
                    temperature REAL,
                    state TEXT,
                    speed INTEGER
                );

                CREATE TABLE IF NOT EXISTS abb_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    voltage_l1 REAL,
                    voltage_l2 REAL,
                    voltage_l3 REAL,
                    current_l1 REAL,
                    current_l2 REAL,
                    current_l3 REAL,
                    active_power REAL
                );

                CREATE TABLE IF NOT EXISTS sensors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    device TEXT,
                    temperature REAL,
                    humidity REAL,
                    dew_point REAL
                );

                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    level TEXT,
                    component TEXT,
                    message TEXT
                );

                CREATE TABLE IF NOT EXISTS llm_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    role TEXT,
                    content TEXT
                );
                """
            )
            conn.commit()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.cfg.path)
        try:
            yield conn
        finally:
            conn.close()

    def insert_event(self, level: str, component: str, message: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO events(level, component, message) VALUES (?, ?, ?)",
                (level, component, message),
            )
            conn.commit()

    def insert_inverter_metrics(self, metrics: Dict[str, Optional[float]]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO inverter_metrics(frequency, current, temperature, state, speed)
                VALUES (:frequency, :current, :temperature, :state, :speed)
                """,
                metrics,
            )
            conn.commit()

    def insert_abb_metrics(self, metrics: Dict[str, Optional[float]]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO abb_metrics(
                    voltage_l1, voltage_l2, voltage_l3,
                    current_l1, current_l2, current_l3,
                    active_power
                )
                VALUES (
                    :voltage_l1, :voltage_l2, :voltage_l3,
                    :current_l1, :current_l2, :current_l3,
                    :active_power
                )
                """,
                metrics,
            )
            conn.commit()

    def insert_sensor_metrics(self, rows: Iterable[Dict[str, Optional[float]]]) -> None:
        with self._connect() as conn:
            conn.executemany(
                "INSERT INTO sensors(device, temperature, humidity, dew_point) VALUES (:device, :temperature, :humidity, :dew_point)",
                rows,
            )
            conn.commit()

    def insert_llm_message(self, role: str, content: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO llm_messages(role, content) VALUES (?, ?)",
                (role, content),
            )
            conn.commit()
