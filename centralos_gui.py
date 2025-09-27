"""CentralOS-style desktop GUI that consumes the modular platform REST API."""

from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime
from typing import Any, Dict, Iterable, Optional

from tkinter import messagebox

import requests
import ttkbootstrap as tb
from ttkbootstrap.constants import BOTH, END, LEFT, RIGHT, TOP, W

API_BASE_DEFAULT = "http://localhost:8000/api/v1"
REFRESH_INTERVAL_SECONDS = 5


def format_float(value: Any, suffix: str = "", precision: int = 2) -> str:
    """Helper to format numbers gracefully."""
    try:
        if value is None:
            return "---"
        number = float(value)
        return f"{number:.{precision}f}{suffix}"
    except (TypeError, ValueError):
        return str(value) if value not in (None, "") else "---"


class CentralOSGUI:
    """Tkinter/ttkbootstrap GUI that mirrors the legacy CentralOS layout."""

    def __init__(self, root: tb.Window, api_base: Optional[str] = None) -> None:
        self.root = root
        self.api_base = api_base or os.getenv("CENTRALOS_API_BASE", API_BASE_DEFAULT)
        self.session = requests.Session()

        self.refresh_interval = int(os.getenv("CENTRALOS_REFRESH", REFRESH_INTERVAL_SECONDS))
        self._refresh_job: Optional[int] = None
        self._fetch_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        self.root.title("CentralOS - Bitcoin Mining Automation")
        self.root.state("zoomed")

        self.status_var = tb.StringVar(value="Conectando à API...")
        self.last_update_var = tb.StringVar(value="Última atualização: --:--:--")
        self._status_base = self.status_var.get()
        self._last_update_text = self.last_update_var.get()

        self._build_layout()
        self._schedule_refresh(initial=True)

    # ------------------------------------------------------------------
    # Layout helpers
    # ------------------------------------------------------------------
    def _build_layout(self) -> None:
        notebook = tb.Notebook(self.root)
        notebook.pack(fill=BOTH, expand=True)

        self.frames: Dict[str, tb.Frame] = {}
        for tab in ("Elétrico", "Ambiente", "F2Pool", "ASICs", "Controles"):
            frame = tb.Frame(notebook, padding=20)
            notebook.add(frame, text=tab)
            self.frames[tab] = frame

        self._build_electric_tab()
        self._build_environment_tab()
        self._build_pool_tab()
        self._build_asic_tab()
        self._build_controls_tab()

        status_bar = tb.Frame(self.root, padding=(10, 5))
        status_bar.pack(fill=BOTH)
        tb.Label(status_bar, textvariable=self.status_var, anchor=W).pack(side=LEFT)
        tb.Label(status_bar, textvariable=self.last_update_var, anchor=W).pack(side=RIGHT)

    def _build_electric_tab(self) -> None:
        frame = self.frames["Elétrico"]
        header = tb.Label(frame, text="Multimedidor ABB", font=("Segoe UI", 22, "bold"))
        header.pack(side=TOP, anchor=W)

        self.abb_vars = {
            "voltage": tb.StringVar(value="Tensão: ---"),
            "current": tb.StringVar(value="Corrente: ---"),
            "power": tb.StringVar(value="Potência: ---"),
            "frequency": tb.StringVar(value="Frequência: ---"),
            "energy": tb.StringVar(value="Energia: ---"),
        }

        for var in self.abb_vars.values():
            tb.Label(frame, textvariable=var, font=("Segoe UI", 18)).pack(anchor=W, pady=4)

    def _build_environment_tab(self) -> None:
        frame = self.frames["Ambiente"]
        tb.Label(frame, text="Sensores BLE", font=("Segoe UI", 22, "bold")).pack(anchor=W)

        columns = ("local", "temperatura", "umidade", "bateria", "sinal", "atualizado")
        self.env_tree = tb.Treeview(
            frame,
            columns=columns,
            show="headings",
            height=12,
            bootstyle="info",
        )
        headings = {
            "local": "Local",
            "temperatura": "Temperatura (°C)",
            "umidade": "Umidade (%)",
            "bateria": "Bateria (%)",
            "sinal": "RSSI (dBm)",
            "atualizado": "Atualizado",
        }
        for column, title in headings.items():
            self.env_tree.heading(column, text=title)
            self.env_tree.column(column, width=160 if column != "local" else 200, anchor="center")
        self.env_tree.pack(fill=BOTH, expand=True, pady=10)

    def _build_pool_tab(self) -> None:
        frame = self.frames["F2Pool"]
        tb.Label(frame, text="Status da Pool", font=("Segoe UI", 22, "bold")).pack(anchor=W)

        self.pool_vars = {
            "current": tb.StringVar(value="Hashrate Atual: --- TH/s"),
            "h24": tb.StringVar(value="Hashrate 24h: --- TH/s"),
            "workers": tb.StringVar(value="Workers: ---"),
            "shares": tb.StringVar(value="Shares: Aceitas --- / Rejeitadas ---"),
            "efficiency": tb.StringVar(value="Eficiência: ---"),
            "last_share": tb.StringVar(value="Último share: ---"),
        }

        for var in self.pool_vars.values():
            tb.Label(frame, textvariable=var, font=("Segoe UI", 18)).pack(anchor=W, pady=4)

    def _build_asic_tab(self) -> None:
        frame = self.frames["ASICs"]
        tb.Label(frame, text="Mineradores", font=("Segoe UI", 22, "bold")).pack(anchor=W)

        summary_frame = tb.Frame(frame)
        summary_frame.pack(fill=BOTH, pady=(10, 15))
        self.asic_summary_vars = {
            "total": tb.StringVar(value="Total: ---"),
            "ativos": tb.StringVar(value="Ativos: ---"),
            "hashrate": tb.StringVar(value="Hashrate Total: --- TH/s"),
            "power": tb.StringVar(value="Consumo Total: --- kW"),
            "temp": tb.StringVar(value="Temperatura Média: --- °C"),
        }
        for var in self.asic_summary_vars.values():
            tb.Label(summary_frame, textvariable=var, font=("Segoe UI", 14)).pack(side=LEFT, padx=10)

        columns = (
            "id",
            "ip",
            "modelo",
            "status",
            "hashrate",
            "power",
            "temp",
            "fan",
            "uptime",
        )
        self.asic_tree = tb.Treeview(
            frame,
            columns=columns,
            show="headings",
            height=14,
            bootstyle="secondary",
        )
        headings = {
            "id": "ID",
            "ip": "IP",
            "modelo": "Modelo",
            "status": "Status",
            "hashrate": "Hashrate (TH/s)",
            "power": "Potência (W)",
            "temp": "Temp (°C)",
            "fan": "Fan (%)",
            "uptime": "Uptime",
        }
        for column, title in headings.items():
            self.asic_tree.heading(column, text=title)
            width = 120
            if column in {"modelo", "status"}:
                width = 160
            if column == "id":
                width = 140
            self.asic_tree.column(column, width=width, anchor="center")
        self.asic_tree.pack(fill=BOTH, expand=True)

    def _build_controls_tab(self) -> None:
        frame = self.frames["Controles"]
        tb.Label(frame, text="Ações Rápidas", font=("Segoe UI", 22, "bold")).pack(anchor=W)

        buttons = tb.Frame(frame)
        buttons.pack(pady=20)

        tb.Button(
            buttons,
            text="Atualizar agora",
            command=self._manual_refresh,
            bootstyle="primary-outline",
            width=18,
        ).pack(side=LEFT, padx=10)

        tb.Button(
            buttons,
            text="Sleep em todos ASICs",
            command=lambda: self._trigger_action("/asic/sleep-all", "Todos os ASICs em sleep"),
            bootstyle="warning-outline",
            width=22,
        ).pack(side=LEFT, padx=10)

        tb.Button(
            buttons,
            text="Retomar todos ASICs",
            command=lambda: self._trigger_action("/asic/resume-all", "ASICs retomados"),
            bootstyle="success-outline",
            width=22,
        ).pack(side=LEFT, padx=10)

        tb.Button(
            buttons,
            text="Sair",
            command=self._exit,
            bootstyle="danger",
            width=12,
        ).pack(side=LEFT, padx=10)

    # ------------------------------------------------------------------
    # Refresh logic
    # ------------------------------------------------------------------
    def _schedule_refresh(self, initial: bool = False) -> None:
        if self._stop_event.is_set():
            return

        if not initial and self._refresh_job is not None:
            self.root.after_cancel(self._refresh_job)

        self._launch_fetch_thread()
        self._refresh_job = self.root.after(self.refresh_interval * 1000, self._schedule_refresh)

    def _manual_refresh(self) -> None:
        self._launch_fetch_thread(force=True)

    def _launch_fetch_thread(self, force: bool = False) -> None:
        if self._fetch_thread and self._fetch_thread.is_alive():
            if not force:
                return
            self._stop_event.set()
            self._fetch_thread.join(timeout=1)
            self._stop_event.clear()

        self._fetch_thread = threading.Thread(target=self._fetch_data, daemon=True)
        self._fetch_thread.start()

    def _fetch_data(self) -> None:
        start_time = time.time()
        realtime = self._request_json("realtime")
        overview = self._request_json("dashboard/overview")
        alerts = self._request_json("alerts") or []
        health = self._request_json("health", root=True)

        payload = {
            "realtime": realtime,
            "overview": overview,
            "alerts": alerts,
            "health": health,
            "latency": time.time() - start_time,
        }
        if not self._stop_event.is_set():
            self.root.after(0, lambda: self._apply_update(payload))

    def _request_json(self, endpoint: str, root: bool = False) -> Optional[Any]:
        url = self._normalize_url(endpoint, root=root)
        try:
            response = self.session.get(url, timeout=5)
            response.raise_for_status()
            if response.headers.get("content-type", "").startswith("application/json"):
                return response.json()
            return json.loads(response.text)
        except requests.RequestException as exc:
            self.root.after(
                0,
                lambda: self.status_var.set(
                    f"Falha ao conectar ({endpoint}): {exc}"[:160]
                ),
            )
            return None
        except json.JSONDecodeError:
            return None

    def _normalize_url(self, endpoint: str, root: bool = False) -> str:
        if endpoint.startswith("http"):
            return endpoint

        base = self.api_base.rstrip("/")
        path = endpoint.strip("/")

        if root:
            if "/api/" in base:
                base = base.split("/api/")[0]
            else:
                base = "/".join(base.split("/")[:-1])
            return f"{base}/{path}" if path else base

        return f"{base}/{path}" if path else base

    # ------------------------------------------------------------------
    # Update UI
    # ------------------------------------------------------------------
    def _apply_update(self, payload: Dict[str, Any]) -> None:
        realtime = payload.get("realtime") or {}
        overview = payload.get("overview") or {}
        health = payload.get("health") or {}
        latency = payload.get("latency", 0.0)

        self._update_status(health, latency)
        self._update_electric(realtime.get("abb"))
        self._update_environment(realtime.get("ble"))
        self._update_pool(realtime.get("pool"))
        self._update_asics(realtime.get("asic"))

        timestamp = datetime.now().strftime("%H:%M:%S")
        self._last_update_text = f"Última atualização: {timestamp}"
        self.last_update_var.set(self._last_update_text)
        self._update_overview(overview)

    def _update_status(self, health: Dict[str, Any], latency: float) -> None:
        if not health:
            self.status_var.set("API indisponível")
            return
        status = health.get("status", "desconhecido")
        components = health.get("components", {})
        collectors = components.get("collectors", {})
        active = sum(1 for ok in collectors.values() if ok)
        latency_ms = int(latency * 1000)
        self._status_base = (
            f"Status: {status.upper()} | Coletores ativos: {active} | Latência API: {latency_ms} ms"
        )
        self.status_var.set(self._status_base)

    def _update_electric(self, abb: Optional[Dict[str, Any]]) -> None:
        data = {}
        if abb:
            data = abb.get("data", abb)
        mappings = {
            "voltage": ("voltage", "V"),
            "current": ("current", "A"),
            "power": ("power", "W"),
            "frequency": ("frequency", "Hz"),
            "energy": ("energy", "kWh"),
        }
        for key, (field, unit) in mappings.items():
            value = data.get(field)
            text = f"{field.capitalize()}: {format_float(value, f' {unit}') if value is not None else '---'}"
            self.abb_vars[key].set(text.replace("_", " "))

    def _update_environment(self, ble: Optional[Any]) -> None:
        self.env_tree.delete(*self.env_tree.get_children())
        if not ble:
            return

        if isinstance(ble, dict):
            items = ble.items()
        elif isinstance(ble, Iterable):
            items = enumerate(ble)
        else:
            items = []

        for key, sensor in items:
            if isinstance(sensor, dict):
                name = (
                    sensor.get("name")
                    or sensor.get("location")
                    or sensor.get("mac")
                    or str(key)
                )
                temp = format_float(sensor.get("temperature"), "", 1)
                hum = format_float(sensor.get("humidity"), "", 1)
                battery = format_float(sensor.get("battery"), "", 0)
                rssi = sensor.get("rssi") or sensor.get("signal") or sensor.get("signal_strength")
                updated = sensor.get("timestamp") or sensor.get("last_seen")
            else:
                name = str(key)
                temp = hum = battery = rssi = updated = "---"

            if isinstance(updated, str):
                display_time = updated
            elif isinstance(updated, (int, float)):
                display_time = datetime.fromtimestamp(updated).isoformat()
            elif isinstance(updated, datetime):
                display_time = updated.strftime("%H:%M:%S")
            else:
                display_time = "---"

            self.env_tree.insert(
                "",
                END,
                values=(
                    name,
                    temp,
                    hum,
                    battery,
                    rssi if rssi is not None else "---",
                    display_time,
                ),
            )

    def _update_pool(self, pool: Optional[Dict[str, Any]]) -> None:
        if not pool:
            for var in self.pool_vars.values():
                var.set(var.get().split(":")[0] + ": ---")
            return

        current = format_float(pool.get("current_hashrate_th_s"), " TH/s")
        h24 = format_float(pool.get("h24_hashrate_th_s"), " TH/s")
        workers = f"{pool.get('active_workers', '---')}/{pool.get('total_workers', '---')}"
        shares = f"Aceitas {pool.get('shares_accepted', '---')} / Rejeitadas {pool.get('shares_rejected', '---')}"
        efficiency_value = pool.get("efficiency")
        efficiency = f"{float(efficiency_value) * 100:.1f}%" if efficiency_value is not None else "---"
        last_share = pool.get("last_share_time") or "---"

        if isinstance(last_share, (int, float)):
            last_share = datetime.fromtimestamp(last_share).strftime("%d/%m %H:%M")
        elif isinstance(last_share, datetime):
            last_share = last_share.strftime("%d/%m %H:%M")

        self.pool_vars["current"].set(f"Hashrate Atual: {current}")
        self.pool_vars["h24"].set(f"Hashrate 24h: {h24}")
        self.pool_vars["workers"].set(f"Workers: {workers}")
        self.pool_vars["shares"].set(f"Shares: {shares}")
        self.pool_vars["efficiency"].set(f"Eficiência: {efficiency}")
        self.pool_vars["last_share"].set(f"Último share: {last_share}")

    def _update_asics(self, asic: Optional[Dict[str, Any]]) -> None:
        self.asic_tree.delete(*self.asic_tree.get_children())
        if not asic:
            for var in self.asic_summary_vars.values():
                base = var.get().split(":")[0]
                var.set(f"{base}: ---")
            return

        miners = asic.get("miners", [])
        total = asic.get("total_miners", len(miners))
        active = asic.get("active_miners", sum(1 for m in miners if m.get("status") == "active"))
        total_hashrate = format_float(asic.get("total_hashrate"), " TH/s")
        power_value = asic.get("total_power")
        total_power_kw = format_float(power_value / 1000 if power_value is not None else None, " kW")
        avg_temp = format_float(asic.get("avg_temperature"), " °C")

        self.asic_summary_vars["total"].set(f"Total: {total}")
        self.asic_summary_vars["ativos"].set(f"Ativos: {active}")
        self.asic_summary_vars["hashrate"].set(f"Hashrate Total: {total_hashrate}")
        self.asic_summary_vars["power"].set(f"Consumo Total: {total_power_kw}")
        self.asic_summary_vars["temp"].set(f"Temperatura Média: {avg_temp}")

        for miner in miners:
            self.asic_tree.insert(
                "",
                END,
                values=(
                    miner.get("id"),
                    miner.get("ip"),
                    miner.get("model"),
                    miner.get("status"),
                    format_float(miner.get("hashrate"), "", 2),
                    format_float(miner.get("power"), "", 0),
                    format_float(miner.get("temperature"), "", 1),
                    format_float(miner.get("fan_speed"), "", 0),
                    miner.get("uptime", "---"),
                ),
            )

    def _update_overview(self, overview: Dict[str, Any]) -> None:
        if not overview:
            return
        alerts = overview.get("alerts_count")
        uptime = overview.get("uptime")
        status_text = self._status_base
        if alerts is not None:
            status_text = f"{status_text} | Alertas ativos: {alerts}"
        self.status_var.set(status_text)

        if uptime:
            hours = format_float(float(uptime) / 3600, " h", 1)
            self.last_update_var.set(f"{self._last_update_text} | Uptime: {hours}")
        else:
            self.last_update_var.set(self._last_update_text)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def _trigger_action(self, endpoint: str, success_message: str) -> None:
        url = self._normalize_url(endpoint)
        try:
            response = self.session.post(url, timeout=5)
            response.raise_for_status()
            messagebox.showinfo("CentralOS", success_message)
            self._launch_fetch_thread(force=True)
        except requests.RequestException as exc:
            messagebox.showerror("CentralOS", f"Falha ao enviar comando: {exc}")

    def _exit(self) -> None:
        self._stop_event.set()
        if self._fetch_thread and self._fetch_thread.is_alive():
            self._fetch_thread.join(timeout=1)
        self.root.quit()


def main() -> None:
    window = tb.Window(themename=os.getenv("CENTRALOS_THEME", "darkly"))
    gui = CentralOSGUI(window)
    window.protocol("WM_DELETE_WINDOW", gui._exit)
    window.mainloop()


if __name__ == "__main__":
    main()
