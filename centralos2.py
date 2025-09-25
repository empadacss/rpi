#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Controle e Monitoramento Unificado
==============================================

Funcionalidades:
  - Monitoramento em tempo real do inversor/exaustor (Modbus TCP)
  - Monitoramento do multimedidor ABB M1M20 (Modbus TCP via adaptador USR‑TCP232‑302) com histórico CSV
  - Controle do exaustor (ajuste de velocidade, partida/desligamento)
  - Controle e status das ASICs (adição, remoção, comandos "sleep"/"resume" e escaneamento de rede)
  - Agendamentos (rotinas de automação)
  - Consulta de dados F2Pool:
      * Dashboard: exibe em tempo real o hashrate (convertido para TH/s com duas casas decimais e vírgula),
        o hashrate das últimas 24h e o número de ASICs conectadas.
      * Aba de Relatórios: gera e exibe o histórico completo dos dados da API F2Pool.
  - Monitoramento Ambiental via BLE dos sensores Xiaomi:
      - Exibe temperatura, umidade e calcula o ponto de orvalho em tempo real.
  - Automação de Segurança:
      1. Se o inversor não estiver em RUN e ASICs estiverem minerando, gera log/alerta e coloca as ASICs em sleep.
      2. Se a umidade for ≥ 90%, força o exaustor a 20% de velocidade.
      3. Se a diferença entre a temperatura ambiente e o ponto de orvalho for inferior a 4°C, força o exaustor a 10%.
  - Interface gráfica moderna (ttkbootstrap – tema "flatly") com canvas/scrollbar e menus para acesso aos relatórios.
  - Relatórios podem ser visualizados na interface e exportados para CSV.
  - Integração com uma LLM para leitura dos logs e interação com o sistema.

Autor: [Seu Nome]
Data: 2025-02-17
"""

# ---------------------------
# IMPORTAÇÕES E CONFIGURAÇÕES INICIAIS
# ---------------------------
import os, sys, re, json, time, math, datetime, csv, struct, asyncio, logging, socket
from threading import Thread, Lock
from functools import partial
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib3
import schedule
import urllib3
import schedule

# ——— Diretório onde serão salvos TODOS os CSVs ———
CSV_DIR = "/home/ipc/Desktop/central/logs_csv"
os.makedirs(CSV_DIR, exist_ok=True)
# ————————————————————————————————————————————
logging.getLogger("urllib3").setLevel(logging.ERROR)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

session = requests.Session()
retries = Retry(total=0, backoff_factor=0)
session.mount('http://', HTTPAdapter(max_retries=retries))

# Tkinter e ttkbootstrap
try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    import ttkbootstrap as tb
except ImportError:
    print("Erro ao importar tkinter/ttkbootstrap.")
    sys.exit(1)

# pymodbus
try:
    from pymodbus.client import ModbusSerialClient as ModbusRTU
    from pymodbus.client import ModbusTcpClient   as ModbusTCP

except ImportError:
    print("Erro ao importar pymodbus.")
    sys.exit(1)

# Bleak para BLE
try:
    from bleak import BleakScanner
    BLE_SUPPORTED = True
except ImportError:
    BLE_SUPPORTED = False
    print("Aviso: bleak não está instalado.")

# atc_mi_interface
try:
    from atc_mi_interface import general_format, atc_mi_advertising_format
except Exception as e:
    print("Erro ao importar atc_mi_interface:", e)
    sys.exit(1)

# ---------------------------
# CONFIGURAÇÕES GERAIS
# ---------------------------
IP_INVERSOR = '192.168.0.111'
PORTA_MODBUS = 502
ABB_SENSOR_IP = '192.168.0.108'
ABB_SENSOR_PORT = 503

LOG_FILE = "logs.txt"
MAX_CON_FAIL_SECONDS = 30

COIN = 'bitcoin'
MINING_USER_NAME = 'ypc321'
API_TOKEN = '2r58tvam1im5dxx4d4l61jmm7p6huhc10h70lorxj6ki6fsleg2vhvcay1uhmx4j'

# ---------------------------
# VARIÁVEIS GLOBAIS
# ---------------------------
g_lock = Lock()
g_values = {
    "frequencia": "--",
    "corrente": "--",
    "temperatura": "--",
    "estado_inversor": "--",
    "hashrate": "--",
    "hashrate_24h": "--",
    "workers": "--/--",
    "potencia_ativa": "--",
    "exaustor_velocidade": "100%"
}
g_sensor1_temp = "--"
g_sensor1_hum  = "--"
g_sensor1_dew  = "--"
g_sensor2_temp = "--"
g_sensor2_hum  = "--"
g_sensor2_dew  = "--"

exaustor = None
root = None

ASICs = []
rotinas_automacao = []
sensor_ble_data = {}

# Registradores inversor/exaustor
ENDERECO_REG_VELOCIDADE    = 685
ENDERECO_REG_COMANDO       = 684
ENDERECO_REG_FREQUENCIA    = 5
ENDERECO_REG_CORRENTE      = 3
ENDERECO_REG_TENSAO        = 7
ENDERECO_REG_TEMPERATURA   = 30
ENDERECO_REG_ESTADO        = 6
ENDERECO_REG_POTENCIOMETRO = 100

inverter_states = {
    0: "Ready (Pronto)",
    1: "Run (Execução)",
    2: "Subtensão",
    3: "Falha",
    4: "Autoajuste",
    5: "Configuração",
    6: "FrenagemCC",
    7: "Reservado",
    8: "FireMode"
}

# Registradores multimedidor ABB
ABB_REGISTERS = {
    "Voltage L1": 12288,
    "Voltage L2": 12290,
    "Voltage L3": 12292,
    "Current L1": 12304,
    "Current L2": 12306,
    "Current L3": 12308,
    "Active Power Total": 12322,
    "Frequency": 12366,
    "Energy Ativa Direta": 12410,
}

last_abb_ok_time = time.time()
last_inversor_ok_time = time.time()

# ---------------------------
# FUNÇÕES DE LOG
# ---------------------------
def write_log_file(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def log(msg):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_msg = f"[{ts}] {msg}"
    print(full_msg)
    write_log_file(full_msg)

def enviar_alerta_whatsapp(erro_msg):
    log(f"[ALERTA] {erro_msg} (Simulação de envio WhatsApp)")

# ---------------------------
# FUNÇÃO DE CÁLCULO DO PONTO DE ORVALHO
# ---------------------------
def calcular_ponto_orvalho(temp, hum):
    try:
        a = 17.27
        b = 237.7
        gamma = math.log(hum / 100.0) + (a * temp) / (b + temp)
        return (b * gamma) / (a - gamma)
    except Exception:
        return None

# ---------------------------
# FUNÇÃO DE LEITURA MODBUS PARA ABB
# ---------------------------
def read_float32_tcp(addr):
    try:
        client = ModbusTCP(host=ABB_SENSOR_IP, port=ABB_SENSOR_PORT, timeout=3)
        if client.connect():
            response = client.read_holding_registers(addr, count=2, slave=1)
            client.close()
            if response and not response.isError():
                regs = response.registers
                return struct.unpack('>f', struct.pack('>HH', regs[0], regs[1]))[0]
            else:
                return None
        else:
            return None
    except Exception as e:
        log(f"Exceção em read_float32_tcp: {e}")
        return None
# ---------------------------
# CLASSE ASIC
# ---------------------------
class ASIC:
    def __init__(self, ip, token):
        self.ip = ip
        self.token = token
        self.state = "unknown"
    def get_status(self):
        headers = {"Authorization": f"Bearer {self.token}", "Accept": "application/json, text/plain, */*"}
        try:
            url = f"http://{self.ip}/api/v1/status"
            resp = session.get(url, headers=headers, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                self.state = data.get("miner_state", "unknown")
            else:
                self.state = "offline"
                log(f"Erro ao obter status da ASIC {self.ip}: HTTP {resp.status_code}")
        except Exception as e:
            self.state = "offline"
            log(f"Erro ao obter status da ASIC {self.ip}: {e}")
    def send_command(self, command):
        headers = {"Authorization": f"Bearer {self.token}", "Accept": "application/json, text/plain, */*"}
        endpoints = {"sleep": "stop", "resume": "start"}
        endpoint = endpoints.get(command)
        if not endpoint:
            log(f"Comando inválido: {command}")
            return False
        url = f"http://{self.ip}/api/v1/mining/{endpoint}"
        try:
            r = session.post(url, headers=headers, json={}, timeout=5)
            if r.status_code == 200:
                self.get_status()
                return True
            else:
                log(f"Falha ao enviar '{command}' para {self.ip}: HTTP {r.status_code}")
                return False
        except Exception as e:
            log(f"Erro ao enviar '{command}' para {self.ip}: {e}")
            return False

# ---------------------------
# CLASSE EXAUSTOR
# ---------------------------
class Exaustor:
    def __init__(self, ip, port, blade_image_path=None):
        self.ip = ip
        self.port = port
        self.velocidade = 100
        self.estado = 1
        self.blade_image = None
        self.blade_photo = None
        if blade_image_path and os.path.exists(blade_image_path):
            try:
                from PIL import Image, ImageTk
                self.blade_image = Image.open(blade_image_path)
                self.blade_photo = ImageTk.PhotoImage(self.blade_image)
            except Exception as e:
                log(f"Erro ao carregar a imagem das pás: {e}")
    def ajustar_velocidade(self, valor):
        global last_inversor_ok_time
        try:
            self.velocidade = int(float(valor))
            reg_val = int((self.velocidade / 100) * 9999)
            client = ModbusTCP(self.ip, port=self.port)
            if client.connect():
                client.write_register(ENDERECO_REG_VELOCIDADE, reg_val, slave=1)
                client.close()
                with g_lock:
                    g_values["exaustor_velocidade"] = f"{self.velocidade}%"
                log(f"Exaustor ajustado para {self.velocidade}%")
                last_inversor_ok_time = time.time()
            else:
                log(f"Falha ao conectar ao inversor {self.ip}")
        except Exception as e:
            log(f"Erro ao ajustar velocidade do exaustor: {e}")
    def partida_motor(self):
        global last_inversor_ok_time
        try:
            client = ModbusTCP(self.ip, port=self.port)
            if client.connect():
                client.write_register(ENDERECO_REG_COMANDO, 0x0007, slave=1)
                self.estado = 1
                log("Exaustor ligado.")
                client.close()
                last_inversor_ok_time = time.time()
            else:
                log("Falha ao conectar para partida do exaustor.")
        except Exception as e:
            log(f"Erro ao partir motor do exaustor: {e}")
    def desligar_motor(self):
        global last_inversor_ok_time
        try:
            client = ModbusTCP(self.ip, port=self.port)
            if client.connect():
                client.write_register(ENDERECO_REG_COMANDO, 0x0000, slave=1)
                self.estado = 0
                log("Exaustor desligado.")
                client.close()
                last_inversor_ok_time = time.time()
            else:
                log("Falha ao conectar para desligar o exaustor.")
        except Exception as e:
            log(f"Erro ao desligar motor do exaustor: {e}")
    def get_parameters(self):
        global last_inversor_ok_time
        try:
            client = ModbusTCP(self.ip, port=self.port)
            if client.connect():
                freq_data = client.read_holding_registers(ENDERECO_REG_FREQUENCIA, count=1, slave=1)
                corr_data = client.read_holding_registers(ENDERECO_REG_CORRENTE,   count=1, slave=1)
                temp_data = client.read_holding_registers(ENDERECO_REG_TEMPERATURA, count=1, slave=1)
                est_data  = client.read_holding_registers(ENDERECO_REG_ESTADO,      count=1, slave=1)
                client.close()
                if freq_data and not freq_data.isError():
                    last_inversor_ok_time = time.time()
                freq = f"{freq_data.registers[0] / 10.0:.2f}" if (freq_data and not freq_data.isError()) else "--"
                corr = f"{corr_data.registers[0] / 10.0:.2f}" if (corr_data and not corr_data.isError()) else "--"
                temp = f"{temp_data.registers[0] / 10.0:.1f}" if (temp_data and not temp_data.isError()) else "--"
                est_val = None
                if est_data and not est_data.isError():
                    e = est_data.registers[0]
                    self.estado = 1 if e == 1 else 0
                    est_val = e
                return {"frequencia": freq, "corrente": corr, "temperatura": temp, "estado": est_val}
        except Exception as e:
            log(f"Erro ao obter parâmetros do exaustor: {e}")
            return {}

# ---------------------------
# FUNÇÕES DE CONTROLE (BOTÕES)
# ---------------------------
def set_potencia():
    val = potenciometro_entry.get().strip()
    if val.isdigit():
        v = int(val)
        if v < 0:
            v = 0
        if v > 100:
            v = 100
        exaustor.ajustar_velocidade(v)
    else:
        messagebox.showwarning("Aviso", "Valor inválido.")

def alternar_exaustor():
    if exaustor:
        if exaustor.estado == 1:
            exaustor.desligar_motor()
            for a in ASICs:
                a.send_command("sleep")
        else:
            exaustor.partida_motor()
            for a in ASICs:
                a.send_command("resume")

# ---------------------------
# FUNÇÕES DE GERENCIAMENTO DE ASICs
# ---------------------------
def adicionar_asic():
    global ASICs
    def salvar():
        global ASICs
        ip = ip_entry.get().strip()
        token = token_entry.get().strip()
        if not (ip and token):
            messagebox.showwarning("Aviso", "Preencha IP e Token.")
            return
        if not re.match(r"^(?:\d{1,3}\.){3}\d{1,3}$", ip):
            messagebox.showwarning("Aviso", "IP inválido.")
            return
        a = ASIC(ip, token)
        a.get_status()
        ASICs.append(a)
        salvar_asics()
        log(f"ASIC {ip} adicionada.")
        top.destroy()
        atualizar_status_asics()
    top = tb.Toplevel(root)
    top.title("Adicionar ASIC")
    top.geometry("300x180")
    tk.Label(top, text="IP:", font=("Helvetica", 12)).pack(pady=5)
    ip_entry = tb.Entry(top, font=("Helvetica", 12))
    ip_entry.pack()
    tk.Label(top, text="Token:", font=("Helvetica", 12)).pack(pady=5)
    token_entry = tb.Entry(top, show="*", font=("Helvetica", 12))
    token_entry.pack()
    tb.Button(top, text="Salvar", command=salvar, bootstyle="success").pack(pady=10, fill="x")

def remover_asic():
    global ASICs
    if not ASICs:
        messagebox.showinfo("Info", "Nenhuma ASIC cadastrada.")
        return
    top = tb.Toplevel(root)
    top.title("Remover ASIC")
    lb = tk.Listbox(top, font=("Helvetica", 12))
    for a in ASICs:
        lb.insert(tk.END, a.ip)
    lb.pack(fill="both", expand=True)
    def confirm():
        global ASICs
        sel = lb.curselection()
        if sel:
            ip = lb.get(sel[0])
            for a in ASICs:
                if a.ip == ip:
                    ASICs.remove(a)
                    salvar_asics()
                    log(f"ASIC {ip} removida.")
                    top.destroy()
                    atualizar_status_asics()
                    return
    tb.Button(top, text="Remover", command=confirm, bootstyle="danger").pack(pady=5, fill="x")

def salvar_asics():
    try:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "asics.json")
        with open(path, "w", encoding="utf-8") as f:
            data = [{"ip": a.ip, "token": a.token} for a in ASICs]
            json.dump(data, f, indent=4)
        log("Lista de ASICs salva.")
    except Exception as e:
        log(f"Erro ao salvar ASICs: {e}")

def carregar_asics():
    global ASICs
    try:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "asics.json")
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                json.dump([], f)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        ASICs.clear()
        for d in data:
            ip = d.get("ip")
            token = d.get("token")
            if ip and token:
                a = ASIC(ip, token)
                a.get_status()
                ASICs.append(a)
        log("Lista de ASICs carregada.")
    except Exception as e:
        log(f"Erro ao carregar ASICs: {e}")

def atualizar_status_asics():
    global asic_status_frame
    if asic_status_frame:
        for widget in asic_status_frame.winfo_children():
            widget.destroy()
        row = 0
        for a in ASICs:
            lbl = tb.Label(asic_status_frame, text=f"IP: {a.ip} | Estado: {a.state}", font=("Helvetica", 12))
            lbl.grid(row=row, column=0, sticky="w", padx=5, pady=2)
            row += 1

# ---------------------------
# FUNÇÕES DE ROTINAS (AGENDAMENTOS)
# ---------------------------
def adicionar_rotina_automacao_gui():
    global rotinas_automacao, rotinas_var
    def salvar():
        global rotinas_automacao, rotinas_var
        h = horario_entry.get().strip()
        v = vel_entry.get().strip()
        a = acao_entry.get().strip().lower()
        ds = [d for d, var in vars_dias if var.get()]
        if not h or not v or not a or not ds:
            messagebox.showwarning("Aviso", "Campos incompletos.")
            return
        try:
            time.strptime(h, "%H:%M")
        except:
            messagebox.showerror("Erro", "Horário inválido. Use HH:MM.")
            return
        try:
            vv = int(v)
            if vv < 0 or vv > 100:
                raise ValueError
        except:
            messagebox.showerror("Erro", "Velocidade deve ser 0..100.")
            return
        if a not in ["sleep", "resume"]:
            messagebox.showerror("Erro", "Ação deve ser 'sleep' ou 'resume'.")
            return
        rotinas_automacao.append({"horario": h, "velocidade": vv, "acao": a, "dias": ds})
        for d in ds:
            try:
                getattr(schedule.every(), d.lower()).at(h).do(executar_rotina_automacao, vv, a)
            except Exception as ex:
                log(f"Erro agendando rotina para {d}: {ex}")
        salvar_rotinas_automacao()
        atualizar_lista_rotinas()
        messagebox.showinfo("Info", "Rotina adicionada.")
        ag_win.destroy()
    ag_win = tb.Toplevel(root)
    ag_win.title("Adicionar Rotina de Automação")
    ag_win.geometry("300x400")
    tk.Label(ag_win, text="Horário (HH:MM):", font=("Helvetica", 12)).pack(pady=5)
    horario_entry = tb.Entry(ag_win, font=("Helvetica", 12))
    horario_entry.pack(pady=5)
    tk.Label(ag_win, text="Velocidade (%):", font=("Helvetica", 12)).pack(pady=5)
    vel_entry = tb.Entry(ag_win, font=("Helvetica", 12))
    vel_entry.pack(pady=5)
    tk.Label(ag_win, text="Ação (sleep/resume):", font=("Helvetica", 12)).pack(pady=5)
    acao_entry = tb.Entry(ag_win, font=("Helvetica", 12))
    acao_entry.pack(pady=5)
    dias = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    vars_dias = []
    for d in dias:
        var = tk.BooleanVar()
        chk = tb.Checkbutton(ag_win, text=d, variable=var, font=("Helvetica", 11))
        chk.pack(anchor="w")
        vars_dias.append((d, var))
    tb.Button(ag_win, text="Salvar", command=salvar, bootstyle="success").pack(pady=20, fill="x")

def salvar_rotinas_automacao():
    try:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rotinas_automacao.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rotinas_automacao, f, indent=4)
        log("Rotinas de automação salvas.")
    except Exception as e:
        log(f"Erro ao salvar rotinas: {e}")

def carregar_rotinas_automacao():
    global rotinas_automacao, rotinas_var
    try:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rotinas_automacao.json")
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                json.dump([], f)
        with open(path, "r", encoding="utf-8") as f:
            rotinas_automacao = json.load(f)
        for r in rotinas_automacao:
            for d in r.get("dias", []):
                try:
                    getattr(schedule.every(), d.lower()).at(r["horario"]).do(executar_rotina_automacao, r["velocidade"], r["acao"])
                except Exception as ex:
                    log(f"Erro agendando rotina carregada para {d}: {ex}")
        atualizar_lista_rotinas()
        log("Rotinas de automação carregadas.")
    except Exception as e:
        log(f"Falha ao carregar rotinas: {e}")

def atualizar_lista_rotinas():
    global rotinas_automacao, rotinas_var
    if rotinas_automacao:
        txt = "\n\n".join([f"{r['horario']} | {r['velocidade']}% | {r['acao'].capitalize()} | {', '.join(r['dias'])}" for r in rotinas_automacao])
    else:
        txt = "Nenhuma rotina de automação."
    rotinas_var.set(txt)

def executar_rotina_automacao(velocidade, acao):
    log(f"Executando rotina: {acao} a {velocidade}%")
    if exaustor:
        exaustor.ajustar_velocidade(velocidade)
        if acao == "sleep":
            exaustor.desligar_motor()
            for a in ASICs:
                a.send_command("sleep")
        else:
            exaustor.partida_motor()
            for a in ASICs:
                a.send_command("resume")

# ---------------------------
# FUNÇÕES F2POOL – MONITORAMENTO E HISTÓRICO
# ---------------------------
def obter_dados_f2pool():
    try:
        url_info = 'https://api.f2pool.com/v2/hash_rate/info'
        url_workers = 'https://api.f2pool.com/v2/hash_rate/worker/list'
        headers = {'Content-Type': 'application/json', 'F2P-API-SECRET': API_TOKEN}
        payload = {'mining_user_name': MINING_USER_NAME, 'currency': COIN}
        ri = session.post(url_info, headers=headers, json=payload, timeout=10)
        rw = session.post(url_workers, headers=headers, json=payload, timeout=10)
        if ri.status_code == 200:
            di = ri.json()
            info = di.get("info", {})
            rt = info.get("hash_rate")
            h24 = info.get("h24_hash_rate")
            with g_lock:
                g_values["hashrate"] = f"{(rt/1e12):.2f}".replace('.', ',') if rt is not None else "--"
                g_values["hashrate_24h"] = f"{(h24/1e12):.2f}".replace('.', ',') if h24 is not None else "--"
            log("Dados F2Pool atualizados.")
        else:
            with g_lock:
                g_values["hashrate"] = "--"
                g_values["hashrate_24h"] = "--"
        if rw.status_code == 200:
            dw = rw.json()
            workers = dw.get("workers", [])
            active = sum(1 for w in workers if w.get("status") == 0)
            total = len(workers)
            with g_lock:
                g_values["workers"] = f"{active}/{total}"
        else:
            with g_lock:
                g_values["workers"] = "--/--"
        registrar_historico_f2pool(ri.json(), rw.json())
    except Exception as e:
        log(f"Erro ao obter dados F2Pool: {e}")
        with g_lock:
            g_values["hashrate"] = "--"
            g_values["hashrate_24h"] = "--"
            g_values["workers"] = "--/--"

def registrar_historico_f2pool(info_data, workers_data):
    try:
        path = os.path.join(CSV_DIR, "historico_f2pool.csv")
        novo = not os.path.exists(path)
        with open(path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if novo:
                writer.writerow(["Timestamp", "F2Pool Info", "Workers Info"])
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([ts, json.dumps(info_data, separators=(",", ":")), json.dumps(workers_data, separators=(",", ":"))])
    except Exception as e:
        log(f"Erro ao registrar histórico F2Pool: {e}")

def ver_historico_f2pool():
    path = os.path.join(CSV_DIR, "historico_f2pool.csv")
    if not os.path.exists(path):
        messagebox.showinfo("Histórico F2Pool", "Nenhum histórico registrado.")
        return
    with open(path, "r", encoding="utf-8") as f:
        reader = list(csv.reader(f))
    if len(reader) <= 1:
        messagebox.showinfo("Histórico F2Pool", "Nenhum dado registrado.")
        return
    top = tb.Toplevel(root)
    top.title("Histórico F2Pool")
    top.geometry("800x300")
    tree = ttk.Treeview(top, columns=reader[0], show="headings")
    for col in reader[0]:
        tree.heading(col, text=col)
        tree.column(col, width=250, anchor="center")
    tree.pack(fill="both", expand=True)
    for row in reader[-10:]:
        tree.insert("", tk.END, values=row)
    scroll = ttk.Scrollbar(top, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scroll.set)
    scroll.pack(side="right", fill="y")

def atualizar_dados_f2pool_thread():
    while True:
        obter_dados_f2pool()
        time.sleep(60)

# ---------------------------
# RELATÓRIOS – INVERSOR, MULTIMEDIDOR, AMBIENTAL
# ---------------------------
def salvar_historico_inversor(values: dict):
    try:
        path = os.path.join(CSV_DIR, "historico_inversor.csv")
        novo = not os.path.exists(path)
        with open(path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if novo:
                writer.writerow(["Timestamp"] + list(values.keys()))
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([ts] + [values[k] for k in values])
    except Exception as e:
        log(f"Erro ao salvar histórico Inversor: {e}")

def ver_historico_inversor():
    path = os.path.join(CSV_DIR, "historico_inversor.csv")
    if not os.path.exists(path):
        messagebox.showinfo("Histórico Inversor", "Nenhum histórico registrado.")
        return
    with open(path, "r", encoding="utf-8") as f:
        reader = list(csv.reader(f))
    if len(reader) <= 1:
        messagebox.showinfo("Histórico Inversor", "Nenhum dado registrado.")
        return
    top = tb.Toplevel(root)
    top.title("Histórico Inversor")
    top.geometry("800x300")
    tree = ttk.Treeview(top, columns=reader[0], show="headings")
    for col in reader[0]:
        tree.heading(col, text=col)
        tree.column(col, width=250, anchor="center")
    tree.pack(fill="both", expand=True)
    for row in reader[-10:]:
        tree.insert("", tk.END, values=row)
    scroll = ttk.Scrollbar(top, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scroll.set)
    scroll.pack(side="right", fill="y")

def salvar_historico_multimedidor(values: dict):
    try:
        path = os.path.join(CSV_DIR, "historico_multimedidor.csv")
        novo = not os.path.exists(path)
        with open(path, "a", newline="") as f:
            writer = csv.writer(f)
            if novo:
                writer.writerow(["Timestamp"] + list(values.keys()))
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([ts] + [values[k] for k in values])
    except Exception as e:
        log(f"Erro ao salvar histórico Multimedidor: {e}")

def ver_historico_multimedidor():
    path = os.path.join(CSV_DIR, "historico_multimedidor.csv")
    if not os.path.exists(path):
        messagebox.showinfo("Histórico Multimedidor", "Nenhum histórico registrado.")
        return
    with open(path, "r", encoding="utf-8") as f:
        reader = list(csv.reader(f))
    if len(reader) <= 1:
        messagebox.showinfo("Histórico Multimedidor", "Nenhum dado registrado.")
        return
    top = tb.Toplevel(root)
    top.title("Histórico Multimedidor")
    top.geometry("800x300")
    tree = ttk.Treeview(top, columns=reader[0], show="headings")
    for col in reader[0]:
        tree.heading(col, text=col)
        tree.column(col, width=250, anchor="center")
    tree.pack(fill="both", expand=True)
    for row in reader[-10:]:
        tree.insert("", tk.END, values=row)
    scroll = ttk.Scrollbar(top, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scroll.set)
    scroll.pack(side="right", fill="y")

def salvar_historico_ambiental():
    try:
        path = os.path.join(CSV_DIR, "historico_ambiental.csv")
        novo = not os.path.exists(path)
        with open(path, "a", newline="") as f:
            writer = csv.writer(f)
            if novo:
                writer.writerow(["Timestamp", "Sensor MAC", "Temperature (°C)", "Humidity (%)", "Dew Point (°C)"])
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for mac, data in sensor_ble_data.items():
                t = data.get("temperature")
                h = data.get("humidity")
                dp = calcular_ponto_orvalho(t, h) if t is not None and h is not None else None
                writer.writerow([ts, mac, f"{t:.1f}" if t is not None else "--",
                                 f"{h:.1f}" if h is not None else "--",
                                 f"{dp:.1f}" if dp is not None else "--"])
    except Exception as e:
        log(f"Erro ao salvar histórico ambiental: {e}")

def ver_historico_ambiental():
    path = os.path.join(CSV_DIR, "historico_ambiental.csv")
    if not os.path.exists(path):
        messagebox.showinfo("Histórico Ambiental", "Arquivo historico_ambiental.csv não existe.")
        return
    with open(path, "r", encoding="utf-8") as f:
        reader = list(csv.reader(f))
    if len(reader) <= 1:
        messagebox.showinfo("Histórico Ambiental", "Nenhum dado registrado.")
        return
    top = tb.Toplevel(root)
    top.title("Histórico Ambiental")
    top.geometry("800x300")
    tree = ttk.Treeview(top, columns=reader[0], show="headings")
    for col in reader[0]:
        tree.heading(col, text=col)
        tree.column(col, width=250, anchor="center")
    tree.pack(fill="both", expand=True)
    for row in reader[-10:]:
        tree.insert("", tk.END, values=row)
    scroll = ttk.Scrollbar(top, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scroll.set)
    scroll.pack(side="right", fill="y")

# ---------------------------
# MONITORAMENTO DO INVERSOR/EXAUSTOR
# ---------------------------
def monitorar_inversor_thread():
    global last_inversor_ok_time
    while True:
        if exaustor:
            params = exaustor.get_parameters()
            if params:
                with g_lock:
                    g_values["frequencia"] = params.get("frequencia", "--")
                    g_values["corrente"] = params.get("corrente", "--")
                    g_values["temperatura"] = params.get("temperatura", "--")
                    estado = params.get("estado", "--")
                    g_values["estado_inversor"] = f"{estado} - {inverter_states.get(estado, 'Desconhecido')}"
                salvar_historico_inversor(params)
                if isinstance(params.get("estado"), int) and params.get("estado") != 1:
                    log("Segurança: Inversor fora de RUN com ASICs ativas!")
                    enviar_alerta_whatsapp("Inversor fora de RUN. Colocando ASICs em sleep.")
                    for a in ASICs:
                        a.send_command("sleep")
            if (time.time() - last_inversor_ok_time) > MAX_CON_FAIL_SECONDS:
                err = "Inversor/Exaustor sem resposta há +30s!"
                log(err)
                enviar_alerta_whatsapp(err)
                last_inversor_ok_time = time.time() + 999999
        time.sleep(10)

# ---------------------------
# MONITORAMENTO DO MULTIMEDIDOR ABB
# ---------------------------
def monitorar_multimedidor_thread():
    global last_abb_ok_time
    while True:
        try:
            client = ModbusTCP(host=ABB_SENSOR_IP, port=ABB_SENSOR_PORT, timeout=3)
            if not client.connect():
                log("Erro: não foi possível conectar ao ABB M1M20.")
                time.sleep(5)
                continue
        except Exception as e:
            log(f"Erro ao conectar ao ABB M1M20: {e}")
            time.sleep(5)
            continue
        values = {}
        ok = False
        for reg, addr in ABB_REGISTERS.items():
            try:
                response = client.read_holding_registers(addr, count=2, slave=1)
                if response and not response.isError():
                    regs = response.registers
                    val = struct.unpack('>f', struct.pack('>HH', regs[0], regs[1]))[0]
                    values[reg] = f"{val:.2f}"
                    ok = True
                else:
                    values[reg] = "--"
            except Exception:
                values[reg] = "--"
        client.close()
        if ok:
            last_abb_ok_time = time.time()
        with g_lock:
            g_values["potencia_ativa"] = values.get("Active Power Total", "--")
        salvar_historico_multimedidor(values)
        if (time.time() - last_abb_ok_time) > MAX_CON_FAIL_SECONDS:
            err = "Multimedidor ABB sem resposta há +30s!"
            log(err)
            enviar_alerta_whatsapp(err)
            last_abb_ok_time = time.time() + 999999
        time.sleep(2)

# ---------------------------
# MONITORAMENTO AMBIENTAL
# ---------------------------
def monitorar_ambiental():
    global g_sensor1_temp, g_sensor1_hum, g_sensor1_dew
    global g_sensor2_temp, g_sensor2_hum, g_sensor2_dew
    if "A4:C1:38:30:26:23" in sensor_ble_data:
        t1 = sensor_ble_data["A4:C1:38:30:26:23"]["temperature"]
        h1 = sensor_ble_data["A4:C1:38:30:26:23"]["humidity"]
        g_sensor1_temp = f"{t1:.1f} °C"
        g_sensor1_hum  = f"{h1:.1f} %"
        dp1 = calcular_ponto_orvalho(t1, h1)
        g_sensor1_dew = f"{dp1:.1f} °C" if dp1 is not None else "--"
        if h1 >= 90:
            log("Alerta: Umidade ≥ 90% detectada!")
            enviar_alerta_whatsapp("Umidade ≥ 90%. Reduzindo exaustor para 20%.")
            exaustor.ajustar_velocidade(20)
        if dp1 is not None and (t1 - dp1) < 4:
            log("Alerta: Diferença T - DP < 4°C!")
            enviar_alerta_whatsapp("Diferença T - DP < 4°C. Reduzindo exaustor para 10%.")
            exaustor.ajustar_velocidade(10)
    if "A4:C1:38:65:D8:21" in sensor_ble_data:
        t2 = sensor_ble_data["A4:C1:38:65:D8:21"]["temperature"]
        h2 = sensor_ble_data["A4:C1:38:65:D8:21"]["humidity"]
        g_sensor2_temp = f"{t2:.1f} °C"
        g_sensor2_hum  = f"{h2:.1f} %"
        dp2 = calcular_ponto_orvalho(t2, h2)
        g_sensor2_dew = f"{dp2:.1f} °C" if dp2 is not None else "--"
        if h2 >= 90:
            log("Alerta: Umidade ≥ 90% (Sensor 2)!")
            enviar_alerta_whatsapp("Umidade ≥ 90% (Sensor 2). Reduzindo exaustor para 20%.")
            exaustor.ajustar_velocidade(20)
        if dp2 is not None and (t2 - dp2) < 4:
            log("Alerta: Diferença T - DP < 4°C (Sensor 2)!")
            enviar_alerta_whatsapp("Diferença T - DP < 4°C (Sensor 2). Reduzindo exaustor para 10%.")
            exaustor.ajustar_velocidade(10)
            salvar_historico_ambiental()
    root.after(1000, monitorar_ambiental)

# ---------------------------
# ATUALIZAÇÃO DA GUI
# ---------------------------
def update_gui():
    global frequencia_var, corrente_var, temperatura_var, estado_inversor_var
    global hashrate_var, hashrate_24h_var, workers_var, potencia_ativa_var
    global sensor1_temp_var, sensor1_hum_var, sensor1_dew_var, sensor2_temp_var, sensor2_hum_var, sensor2_dew_var
    with g_lock:
        frequencia_var.set(f"Frequência: {g_values.get('frequencia', '--')} Hz")
        corrente_var.set(f"Corrente: {g_values.get('corrente', '--')} A")
        temperatura_var.set(f"Temperatura: {g_values.get('temperatura', '--')} °C")
        estado_inversor_var.set(f"Estado do Inversor: {g_values.get('estado_inversor', '--')}")
        hashrate_var.set(f"Hashrate em Tempo Real: {g_values.get('hashrate', '--')} TH/s")
        hashrate_24h_var.set(f"Hashrate 24h: {g_values.get('hashrate_24h', '--')} TH/s")
        workers_var.set(f"ASICs Conectadas: {g_values.get('workers', '--/--')}")
        potencia_ativa_var.set(f"Potência Ativa Total: {g_values.get('potencia_ativa', '--')} W")
    sensor1_temp_var.set(g_sensor1_temp)
    sensor1_hum_var.set(g_sensor1_hum)
    sensor1_dew_var.set(g_sensor1_dew)
    sensor2_temp_var.set(g_sensor2_temp)
    sensor2_hum_var.set(g_sensor2_hum)
    sensor2_dew_var.set(g_sensor2_dew)
    root.after(1000, update_gui)

# ---------------------------
# THREAD DO SCHEDULE
# ---------------------------
def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

# ---------------------------
# FUNÇÕES BLE
# ---------------------------
def ble_detection_callback(device, advertisement_data):
    mac = device.address.upper()
    frame = None
    if advertisement_data.service_data:
        for uuid, value in advertisement_data.service_data.items():
            frame = value
            break
    elif advertisement_data.manufacturer_data:
        for m_id, value in advertisement_data.manufacturer_data.items():
            frame = value
            break
    if frame and len(frame) >= 11:
        try:
            fmt_label, proc_frame = atc_mi_advertising_format(advertisement_data)
            if not proc_frame:
                return
            mac_bytes = bytes.fromhex(mac.replace(":", ""))
            decoded = general_format.parse(proc_frame, mac_address=mac_bytes, bindkey=None)
            temps = decoded.search_all("^temperature")
            hums = decoded.search_all("^humidity")
            if temps and hums:
                sensor_ble_data[mac] = {"temperature": temps[0], "humidity": hums[0]}
                logging.info(f"Sensor BLE {mac}: Temp={temps[0]}°C, Humid={hums[0]}% ({fmt_label})")
            else:
                logging.debug(f"Sensor BLE {mac}: Campos não encontrados ({fmt_label}).")
        except Exception as e:
            logging.error(f"Erro ao decodificar sensor BLE {mac}: {e}")
    else:
        logging.debug(f"Sensor BLE {mac}: Anúncio sem dados ou formato inválido.")

async def ble_scan_loop():
    scanner = BleakScanner(detection_callback=ble_detection_callback)
    while True:
        try:
            await scanner.start()
            await asyncio.sleep(5)
            await scanner.stop()
        except Exception as e:
            logging.error(f"Erro no scanner BLE: {e}")
        await asyncio.sleep(0.5)

def run_ble_async_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_until_complete(ble_scan_loop())

# ---------------------------
# INTEGRAÇÃO COM LLM (Exemplo de Consulta)
# ---------------------------
def consultar_llm():
    global root
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            logs_content = f.read()
    except Exception as e:
        logs_content = f"Erro ao ler logs: {e}"
    
    prompt = (
        "Você é um assistente técnico especializado em mineração de criptomoedas. "
        "A seguir, estão os registros recentes do sistema:\n\n"
        f"{logs_content}\n\n"
        "Analise os registros, identifique possíveis falhas e sugira ajustes para melhorar a operação dos dispositivos, "
        "incluindo ASICs, exaustores e potência dos equipamentos. "
        "Forneça recomendações detalhadas e, se possível, indique comandos que possam ser executados automaticamente."
    )
    
    headers = {
        "Authorization": "Bearer SUA_CHAVE_API_LLMTOKEN",  # Substitua pela sua chave de API da LLM
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 300,
    }
    
    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
        if response.status_code == 200:
            answer = response.json()["choices"][0]["message"]["content"]
        else:
            answer = f"Erro na API LLM: {response.text}"
    except Exception as e:
        answer = f"Exceção ao chamar a API LLM: {e}"
    
    top = tb.Toplevel(root)
    top.title("Resposta da LLM")
    top.geometry("800x400")
    text_widget = tk.Text(top, wrap="word", font=("Helvetica", 12))
    text_widget.pack(fill="both", expand=True)
    text_widget.insert("1.0", answer)
    text_widget.config(state="disabled")
    log("Consulta à LLM concluída.")

# ---------------------------
# INICIALIZAÇÃO DA INTERFACE GRÁFICA
# ---------------------------
def init_gui():
    global root, logs_text, potenciometro_entry, potenciometro_slider
    global frequencia_var, corrente_var, temperatura_var, estado_inversor_var, status_label_var, exaustor_estado_var
    global hashrate_var, hashrate_24h_var, workers_var, potencia_ativa_var
    global sensor1_temp_var, sensor1_hum_var, sensor1_dew_var, sensor2_temp_var, sensor2_hum_var, sensor2_dew_var
    global exaustor, asic_status_frame, rotinas_var

    style = tb.Style(theme="flatly")
    root = style.master
    root.title("Sistema de Monitoramento Unificado")
    root.attributes('-fullscreen', True)
    root.resizable(True, True)

    canvas = tk.Canvas(root)
    scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)
    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    menubar = tk.Menu(root)
    menu_asic = tk.Menu(menubar, tearoff=0)
    menu_asic.add_command(label="Adicionar ASIC", command=adicionar_asic)
    menu_asic.add_command(label="Remover ASIC", command=remover_asic)
    menu_asic.add_command(label="Escanear Rede", command=lambda: Thread(target=escanear_rede, daemon=True).start())
    menubar.add_cascade(label="ASIC", menu=menu_asic)
    
    menu_llm = tk.Menu(menubar, tearoff=0)
    menu_llm.add_command(label="Consultar LLM", command=consultar_llm)
    menubar.add_cascade(label="LLM", menu=menu_llm)
    
    menu_rot = tk.Menu(menubar, tearoff=0)
    menu_rot.add_command(label="Adicionar Rotina", command=adicionar_rotina_automacao_gui)
    menubar.add_cascade(label="Rotinas", menu=menu_rot)
    
    menu_rel = tk.Menu(menubar, tearoff=0)
    menu_rel.add_command(label="Ver Histórico Inversor", command=ver_historico_inversor)
    menu_rel.add_command(label="Ver Histórico Multimedidor", command=ver_historico_multimedidor)
    menu_rel.add_command(label="Ver Histórico F2Pool", command=ver_historico_f2pool)
    menu_rel.add_command(label="Ver Histórico Ambiental", command=ver_historico_ambiental)
    menubar.add_cascade(label="Relatórios", menu=menu_rel)
    
    menu_op = tk.Menu(menubar, tearoff=0)
    menu_op.add_command(label="Sair", command=root.quit)
    menubar.add_cascade(label="Opções", menu=menu_op)
    root.config(menu=menubar)

    top_frame = tb.Frame(scrollable_frame, padding=10)
    top_frame.pack(side="top", fill="both", expand=True)
    left_frame = tb.Frame(top_frame)
    left_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
    right_frame = tb.Frame(top_frame)
    right_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)

    logs_frame = tb.Labelframe(left_frame, text="Logs do Sistema", bootstyle="info")
    logs_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
    logs_text = tk.Text(logs_frame, font=("Helvetica", 10), wrap="word", state="disabled", bg="#f0f0f0", relief="sunken")
    logs_text.pack(fill="both", expand=True)
    log_scroll = ttk.Scrollbar(logs_frame, orient="vertical", command=logs_text.yview)
    logs_text.configure(yscrollcommand=log_scroll.set)
    log_scroll.pack(side="right", fill="y")

    from PIL import Image, ImageTk
    blade_image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blade.png")
    global exaustor
    exaustor = Exaustor(IP_INVERSOR, PORTA_MODBUS, blade_image_path)

    global frequencia_var, corrente_var, temperatura_var, estado_inversor_var, status_label_var, exaustor_estado_var
    frequencia_var = tk.StringVar(value="Frequência: -- Hz")
    corrente_var = tk.StringVar(value="Corrente: -- A")
    temperatura_var = tk.StringVar(value="Temperatura: -- °C")
    estado_inversor_var = tk.StringVar(value="Estado do Inversor: --")
    status_label_var = tk.StringVar(value="Velocidade: 100%")
    exaustor_estado_var = tk.StringVar(value="Ligado")
    frame_inv = tb.Labelframe(right_frame, text="Inversor/Exaustor", bootstyle="info")
    frame_inv.pack(fill="both", expand=True, padx=5, pady=5)
    tk.Label(frame_inv, textvariable=frequencia_var, font=("Helvetica", 14, "bold"), fg="blue").pack(anchor="w", pady=5)
    tk.Label(frame_inv, textvariable=corrente_var, font=("Helvetica", 14, "bold"), fg="blue").pack(anchor="w", pady=5)
    tk.Label(frame_inv, textvariable=temperatura_var, font=("Helvetica", 14, "bold"), fg="blue").pack(anchor="w", pady=5)
    tk.Label(frame_inv, textvariable=estado_inversor_var, font=("Helvetica", 14, "bold"), fg="blue").pack(anchor="w", pady=5)
    pot_frame = tb.Frame(frame_inv)
    pot_frame.pack(pady=5)
    global potenciometro_slider, potenciometro_entry
    potenciometro_slider = tb.Scale(pot_frame, from_=0, to=100, orient="horizontal", length=200, bootstyle="success",
                                    command=lambda val: exaustor.ajustar_velocidade(val))
    potenciometro_slider.set(100)
    potenciometro_slider.pack(side="left", pady=5)
    potenciometro_entry = tb.Entry(pot_frame, width=5, font=("Helvetica", 12))
    potenciometro_entry.pack(side="left", padx=5)
    potenciometro_entry.insert(0, "100")
    tk.Button(pot_frame, text="Set", font=("Helvetica", 12), command=set_potencia).pack(side="left", padx=5)
    tk.Button(pot_frame, text="Liga/Desliga", font=("Helvetica", 12), command=alternar_exaustor).pack(side="left", padx=5)
    tk.Label(frame_inv, textvariable=status_label_var, font=("Helvetica", 12), fg="dark blue").pack(pady=5)
    tk.Label(frame_inv, textvariable=exaustor_estado_var, font=("Helvetica", 12), fg="dark blue").pack(pady=5)

    global potencia_ativa_var
    potencia_ativa_var = tk.StringVar(value="Potência Ativa Total: -- W")
    frame_abb = tb.Labelframe(right_frame, text="Multimedidor ABB", bootstyle="info")
    frame_abb.pack(fill="both", expand=True, padx=5, pady=5)
    tk.Label(frame_abb, textvariable=potencia_ativa_var, font=("Helvetica", 14, "bold"), fg="red").pack(anchor="w", pady=5)
    def atualizar_abb():
        values = {}
        ok = False
        for reg, addr in ABB_REGISTERS.items():
            val = read_float32_tcp(addr)
            values[reg] = f"{val:.2f}" if val is not None else "--"
            if val is not None:
                ok = True
        if ok:
            global last_abb_ok_time
            last_abb_ok_time = time.time()
        with g_lock:
            g_values["potencia_ativa"] = values.get("Active Power Total", "--")
        salvar_historico_multimedidor(values)
        root.after(2000, atualizar_abb)
    atualizar_abb()

    global sensor1_temp_var, sensor1_hum_var, sensor1_dew_var, sensor2_temp_var, sensor2_hum_var, sensor2_dew_var
    sensor1_temp_var = tk.StringVar(value="-- °C")
    sensor1_hum_var  = tk.StringVar(value="-- %")
    sensor1_dew_var  = tk.StringVar(value="-- °C")
    sensor2_temp_var = tk.StringVar(value="-- °C")
    sensor2_hum_var  = tk.StringVar(value="-- %")
    sensor2_dew_var  = tk.StringVar(value="-- °C")
    frame_amb = tb.Labelframe(right_frame, text="Ambiente (BLE)", bootstyle="info")
    frame_amb.pack(fill="both", expand=True, padx=5, pady=5)
    tk.Label(frame_amb, text="Sensor A4:C1:38:30:26:23", font=("Helvetica", 12, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")
    tk.Label(frame_amb, text="Temp:", font=("Helvetica", 12)).grid(row=1, column=0, padx=5, pady=2, sticky="w")
    tk.Label(frame_amb, textvariable=sensor1_temp_var, font=("Helvetica", 12), fg="green").grid(row=1, column=1, padx=5, pady=2, sticky="w")
    tk.Label(frame_amb, text="Humid:", font=("Helvetica", 12)).grid(row=2, column=0, padx=5, pady=2, sticky="w")
    tk.Label(frame_amb, textvariable=sensor1_hum_var, font=("Helvetica", 12), fg="green").grid(row=2, column=1, padx=5, pady=2, sticky="w")
    tk.Label(frame_amb, text="Ponto de Orvalho:", font=("Helvetica", 12)).grid(row=3, column=0, padx=5, pady=2, sticky="w")
    tk.Label(frame_amb, textvariable=sensor1_dew_var, font=("Helvetica", 12), fg="purple").grid(row=3, column=1, padx=5, pady=2, sticky="w")
    tk.Label(frame_amb, text="Sensor A4:C1:38:65:D8:21", font=("Helvetica", 12, "bold")).grid(row=0, column=2, padx=20, pady=5, sticky="w")
    tk.Label(frame_amb, text="Temp:", font=("Helvetica", 12)).grid(row=1, column=2, padx=5, pady=2, sticky="w")
    tk.Label(frame_amb, textvariable=sensor2_temp_var, font=("Helvetica", 12), fg="green").grid(row=1, column=3, padx=5, pady=2, sticky="w")
    tk.Label(frame_amb, text="Humid:", font=("Helvetica", 12)).grid(row=2, column=2, padx=5, pady=2, sticky="w")
    tk.Label(frame_amb, textvariable=sensor2_hum_var, font=("Helvetica", 12), fg="green").grid(row=2, column=3, padx=5, pady=2, sticky="w")
    tk.Label(frame_amb, text="Ponto de Orvalho:", font=("Helvetica", 12)).grid(row=3, column=2, padx=5, pady=2, sticky="w")
    tk.Label(frame_amb, textvariable=sensor2_dew_var, font=("Helvetica", 12), fg="purple").grid(row=3, column=3, padx=5, pady=2, sticky="w")

    global hashrate_var, hashrate_24h_var, workers_var
    hashrate_var = tk.StringVar(value="Hashrate em Tempo Real: -- TH/s")
    hashrate_24h_var = tk.StringVar(value="Hashrate 24h: -- TH/s")
    workers_var = tk.StringVar(value="ASICs Conectadas: --/--")
    f2p_frame = tb.Labelframe(right_frame, text="Dados da F2Pool", bootstyle="info")
    f2p_frame.pack(fill="both", expand=True, padx=5, pady=5)
    tk.Label(f2p_frame, textvariable=hashrate_var, font=("Helvetica", 14, "bold"), fg="blue").pack(anchor="w", pady=5)
    tk.Label(f2p_frame, textvariable=hashrate_24h_var, font=("Helvetica", 14, "bold"), fg="blue").pack(anchor="w", pady=5)
    tk.Label(f2p_frame, textvariable=workers_var, font=("Helvetica", 14, "bold"), fg="blue").pack(anchor="w", pady=5)

    global asic_status_frame
    asic_frame = tb.Labelframe(right_frame, text="Controle das ASICs", bootstyle="info")
    asic_frame.pack(fill="both", expand=True, padx=5, pady=5)
    cmd_asic = tb.Frame(asic_frame)
    cmd_asic.pack(fill="x", pady=5)
    tk.Button(cmd_asic, text="Sleep All", font=("Helvetica", 12), command=lambda: [a.send_command("sleep") for a in ASICs]).pack(side="left", padx=5)
    tk.Button(cmd_asic, text="Resume All", font=("Helvetica", 12), command=lambda: [a.send_command("resume") for a in ASICs]).pack(side="left", padx=5)
    tk.Button(asic_frame, text="Adicionar ASIC", font=("Helvetica", 12), command=adicionar_asic).pack(fill="x", pady=5)
    tk.Button(asic_frame, text="Remover ASIC", font=("Helvetica", 12), command=remover_asic).pack(fill="x", pady=5)
    asic_status_frame = tb.Frame(asic_frame)
    asic_status_frame.pack(fill="both", expand=True, pady=10)

    global rotinas_var
    rotinas_var = tk.StringVar(value="Nenhuma rotina de automação.")
    rotina_frame = tb.Labelframe(right_frame, text="Rotinas de Automação", bootstyle="info")
    rotina_frame.pack(fill="both", expand=True, padx=5, pady=5)
    tk.Button(rotina_frame, text="Adicionar Rotina", font=("Helvetica", 12), command=adicionar_rotina_automacao_gui).pack(fill="x", pady=5)
    tk.Label(rotina_frame, textvariable=rotinas_var, font=("Helvetica", 12), fg="dark blue").pack(padx=5, pady=5, anchor="w")
    carregar_rotinas_automacao()

    tab_logs = ttk.Frame(scrollable_frame)
    tab_logs.pack(fill="both", expand=True)
    frame_logs2 = tb.Labelframe(tab_logs, text="Logs do Sistema", bootstyle="info")
    frame_logs2.pack(fill="both", expand=True, padx=10, pady=10)
    logs_text.delete("1.0", tk.END)
    logs_text.pack(fill="both", expand=True)
    log_scroll2 = ttk.Scrollbar(frame_logs2, orient="vertical", command=logs_text.yview)
    logs_text.configure(yscrollcommand=log_scroll2.set)
    log_scroll2.pack(side="right", fill="y")
    btn_frame = tb.Frame(tab_logs)
    btn_frame.pack(fill="x", padx=10, pady=5)
    tk.Button(btn_frame, text="Ver Histórico Inversor", font=("Helvetica", 12), command=ver_historico_inversor).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Ver Histórico Multimedidor", font=("Helvetica", 12), command=ver_historico_multimedidor).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Ver Histórico F2Pool", font=("Helvetica", 12), command=ver_historico_f2pool).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Ver Histórico Ambiental", font=("Helvetica", 12), command=ver_historico_ambiental).pack(side="left", padx=5)

    Thread(target=monitorar_multimedidor_thread, daemon=True).start()
    Thread(target=monitorar_inversor_thread, daemon=True).start()
    Thread(target=atualizar_dados_f2pool_thread, daemon=True).start()
    Thread(target=run_schedule, daemon=True).start()
    if BLE_SUPPORTED:
        ble_loop = asyncio.new_event_loop()
        Thread(target=run_ble_async_loop, args=(ble_loop,), daemon=True).start()
    else:
        log("Sensores BLE não funcionarão (bleak ausente).")
    monitorar_ambiental()
    update_gui()
    log("Sistema Iniciado com sucesso!")
    root.mainloop()

# ---------------------------
# FUNÇÃO DE ESCANEAMENTO DE REDE PARA ASICs
# ---------------------------
def escanear_rede():
    global ASICs
    def scan():
        global ASICs
        log("Iniciando escaneamento 192.168.0.x ...")
        found = False
        for i in range(1, 256):
            ip = f"192.168.0.{i}"
            try:
                url = f"http://{ip}/dashboard"
                r = session.get(url, timeout=0.5)
                if r.status_code == 200:
                    if not any(a.ip == ip for a in ASICs):
                        a = ASIC(ip, "TOKEN_POR_PADRAO")
                        a.get_status()
                        ASICs.append(a)
                        salvar_asics()
                        log(f"ASIC encontrada: {ip}")
                        found = True
            except Exception:
                continue
        if not found:
            log("Nenhuma ASIC encontrada no scan.")
        atualizar_status_asics()
    Thread(target=scan, daemon=True).start()

# ---------------------------
# FUNÇÃO MAIN
# ---------------------------
def main():
    carregar_asics()
    init_gui()

if __name__ == "__main__":
    main()
