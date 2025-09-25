#!/usr/bin/env python3
"""
Script de atualização específico para Raspberry Pi
Sistema de Automação para Mineração de Bitcoin
"""

import os
import sys
import json
import shutil
import subprocess
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

class RaspberryPiUpdater:
    """Classe para atualizar o sistema no Raspberry Pi"""
    
    def __init__(self):
        self.base_path = Path("/opt/bitcoin_mining")
        self.backup_path = self.base_path / "backup"
        self.update_path = self.base_path / "updates"
        
        # URLs de atualização
        self.github_repo = "https://api.github.com/repos/seu-usuario/bitcoin-mining-automation"
        self.github_releases = f"{self.github_repo}/releases"
        self.github_latest = f"{self.github_repo}/releases/latest"
        
        # Configurações
        self.auto_backup = True
        self.auto_restart = True
        self.keep_backups = 3
        
    def check_system_requirements(self) -> bool:
        """Verificar requisitos do sistema"""
        print("Verificando requisitos do sistema...")
        
        try:
            # Verificar Python
            python_version = sys.version_info
            if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
                print("❌ Python 3.8+ é necessário")
                return False
            print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
            
            # Verificar Docker
            try:
                result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"✅ Docker: {result.stdout.strip()}")
                else:
                    print("❌ Docker não encontrado")
                    return False
            except FileNotFoundError:
                print("❌ Docker não encontrado")
                return False
            
            # Verificar Docker Compose
            try:
                result = subprocess.run(['docker-compose', '--version'], capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"✅ Docker Compose: {result.stdout.strip()}")
                else:
                    print("❌ Docker Compose não encontrado")
                    return False
            except FileNotFoundError:
                print("❌ Docker Compose não encontrado")
                return False
            
            # Verificar espaço em disco
            disk_usage = shutil.disk_usage(self.base_path)
            free_gb = disk_usage.free / (1024**3)
            if free_gb < 2:
                print(f"❌ Espaço insuficiente: {free_gb:.1f} GB disponível (mínimo: 2 GB)")
                return False
            print(f"✅ Espaço em disco: {free_gb:.1f} GB disponível")
            
            # Verificar memória
            try:
                with open('/proc/meminfo', 'r') as f:
                    meminfo = {}
                    for line in f:
                        if ':' in line:
                            key, value = line.split(':', 1)
                            meminfo[key.strip()] = value.strip()
                
                total_mem = int(meminfo['MemTotal'].split()[0]) / 1024  # MB
                if total_mem < 1024:  # 1 GB
                    print(f"❌ Memória insuficiente: {total_mem:.0f} MB (mínimo: 1024 MB)")
                    return False
                print(f"✅ Memória: {total_mem:.0f} MB")
                
            except Exception as e:
                print(f"⚠️ Erro ao verificar memória: {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao verificar requisitos: {e}")
            return False
    
    def get_current_version(self) -> str:
        """Obter versão atual"""
        try:
            version_file = self.base_path / "VERSION"
            if version_file.exists():
                return version_file.read_text().strip()
            else:
                return "0.0.0"
        except Exception:
            return "0.0.0"
    
    def get_latest_version(self) -> Optional[str]:
        """Obter versão mais recente"""
        try:
            print("Verificando versão mais recente...")
            
            response = requests.get(self.github_latest, timeout=10)
            if response.status_code == 200:
                release_data = response.json()
                version = release_data['tag_name'].lstrip('v')
                print(f"✅ Versão mais recente: {version}")
                return version
            else:
                print(f"❌ Erro ao verificar versão: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Erro ao verificar versão: {e}")
            return None
    
    def download_update(self, version: str) -> Optional[Path]:
        """Baixar atualização"""
        try:
            print(f"Baixando versão {version}...")
            
            # Criar diretório de atualizações
            self.update_path.mkdir(exist_ok=True)
            
            # URL do arquivo de atualização
            download_url = f"{self.github_repo}/archive/refs/tags/v{version}.tar.gz"
            
            # Nome do arquivo
            update_file = self.update_path / f"bitcoin_mining_automation_{version}.tar.gz"
            
            # Baixar arquivo
            response = requests.get(download_url, stream=True, timeout=30)
            if response.status_code == 200:
                with open(update_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                print(f"✅ Download concluído: {update_file}")
                return update_file
            else:
                print(f"❌ Erro ao baixar: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Erro ao baixar atualização: {e}")
            return None
    
    def extract_update(self, update_file: Path) -> Optional[Path]:
        """Extrair atualização"""
        try:
            print("Extraindo atualização...")
            
            # Diretório de extração
            extract_dir = self.update_path / f"extracted_{update_file.stem}"
            extract_dir.mkdir(exist_ok=True)
            
            # Extrair arquivo
            import tarfile
            with tarfile.open(update_file, 'r:gz') as tar:
                tar.extractall(extract_dir)
            
            # Encontrar diretório extraído
            extracted_dirs = list(extract_dir.glob("bitcoin_mining_automation-*"))
            if extracted_dirs:
                source_dir = extracted_dirs[0]
                print(f"✅ Extraído em: {source_dir}")
                return source_dir
            else:
                print("❌ Diretório extraído não encontrado")
                return None
                
        except Exception as e:
            print(f"❌ Erro ao extrair atualização: {e}")
            return None
    
    def backup_current_system(self) -> bool:
        """Fazer backup do sistema atual"""
        if not self.auto_backup:
            return True
        
        try:
            print("Fazendo backup do sistema atual...")
            
            # Executar script de backup
            backup_script = self.base_path / "scripts" / "backup_raspberry_pi.py"
            if backup_script.exists():
                result = subprocess.run([sys.executable, str(backup_script)], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print("✅ Backup concluído")
                    return True
                else:
                    print(f"❌ Erro no backup: {result.stderr}")
                    return False
            else:
                print("⚠️ Script de backup não encontrado")
                return True
                
        except Exception as e:
            print(f"❌ Erro ao fazer backup: {e}")
            return False
    
    def stop_services(self) -> bool:
        """Parar serviços"""
        try:
            print("Parando serviços...")
            
            # Parar serviço Python
            try:
                subprocess.run(['systemctl', 'stop', 'bitcoin-mining-python.service'], 
                             check=True)
                print("✅ Serviço Python parado")
            except subprocess.CalledProcessError:
                print("⚠️ Serviço Python não estava rodando")
            
            # Parar Docker Compose
            try:
                subprocess.run(['docker-compose', 'down'], cwd=self.base_path, check=True)
                print("✅ Docker Compose parado")
            except subprocess.CalledProcessError:
                print("⚠️ Docker Compose não estava rodando")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao parar serviços: {e}")
            return False
    
    def update_files(self, source_dir: Path) -> bool:
        """Atualizar arquivos"""
        try:
            print("Atualizando arquivos...")
            
            # Lista de arquivos/diretórios para atualizar
            update_items = [
                "backend",
                "frontend", 
                "scripts",
                "monitoring",
                "docs",
                "requirements.txt",
                "docker-compose.yml",
                "Dockerfile"
            ]
            
            # Lista de arquivos/diretórios para preservar
            preserve_items = [
                "data",
                "logs",
                "config",
                "reports",
                "backup",
                ".env"
            ]
            
            # Fazer backup dos arquivos importantes
            backup_dir = self.base_path / "update_backup"
            backup_dir.mkdir(exist_ok=True)
            
            for item in preserve_items:
                source_item = self.base_path / item
                if source_item.exists():
                    dest_item = backup_dir / item
                    if source_item.is_dir():
                        shutil.copytree(source_item, dest_item, dirs_exist_ok=True)
                    else:
                        shutil.copy2(source_item, dest_item)
                    print(f"✅ Preservado: {item}")
            
            # Atualizar arquivos
            for item in update_items:
                source_item = source_dir / item
                dest_item = self.base_path / item
                
                if source_item.exists():
                    if dest_item.exists():
                        if dest_item.is_dir():
                            shutil.rmtree(dest_item)
                        else:
                            dest_item.unlink()
                    
                    if source_item.is_dir():
                        shutil.copytree(source_item, dest_item)
                    else:
                        shutil.copy2(source_item, dest_item)
                    
                    print(f"✅ Atualizado: {item}")
            
            # Restaurar arquivos preservados
            for item in preserve_items:
                backup_item = backup_dir / item
                dest_item = self.base_path / item
                
                if backup_item.exists():
                    if dest_item.exists():
                        if dest_item.is_dir():
                            shutil.rmtree(dest_item)
                        else:
                            dest_item.unlink()
                    
                    if backup_item.is_dir():
                        shutil.copytree(backup_item, dest_item)
                    else:
                        shutil.copy2(backup_item, dest_item)
                    
                    print(f"✅ Restaurado: {item}")
            
            # Limpar backup temporário
            shutil.rmtree(backup_dir)
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao atualizar arquivos: {e}")
            return False
    
    def update_dependencies(self) -> bool:
        """Atualizar dependências"""
        try:
            print("Atualizando dependências...")
            
            # Atualizar dependências Python
            requirements_file = self.base_path / "requirements.txt"
            if requirements_file.exists():
                result = subprocess.run([
                    sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("✅ Dependências Python atualizadas")
                else:
                    print(f"⚠️ Erro ao atualizar dependências Python: {result.stderr}")
            
            # Reconstruir imagens Docker
            try:
                subprocess.run(['docker-compose', 'build', '--no-cache'], 
                             cwd=self.base_path, check=True)
                print("✅ Imagens Docker reconstruídas")
            except subprocess.CalledProcessError as e:
                print(f"⚠️ Erro ao reconstruir imagens Docker: {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao atualizar dependências: {e}")
            return False
    
    def update_version_file(self, version: str) -> bool:
        """Atualizar arquivo de versão"""
        try:
            print(f"Atualizando versão para {version}...")
            
            version_file = self.base_path / "VERSION"
            with open(version_file, 'w') as f:
                f.write(version)
            
            print(f"✅ Versão atualizada: {version}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao atualizar versão: {e}")
            return False
    
    def start_services(self) -> bool:
        """Iniciar serviços"""
        if not self.auto_restart:
            return True
        
        try:
            print("Iniciando serviços...")
            
            # Iniciar Docker Compose
            try:
                subprocess.run(['docker-compose', 'up', '-d'], cwd=self.base_path, check=True)
                print("✅ Docker Compose iniciado")
            except subprocess.CalledProcessError as e:
                print(f"❌ Erro ao iniciar Docker Compose: {e}")
                return False
            
            # Aguardar serviços iniciarem
            print("Aguardando serviços iniciarem...")
            import time
            time.sleep(30)
            
            # Verificar status
            try:
                result = subprocess.run(['docker-compose', 'ps'], cwd=self.base_path, 
                                      capture_output=True, text=True)
                print("Status dos containers:")
                print(result.stdout)
            except subprocess.CalledProcessError:
                pass
            
            # Iniciar serviço Python (opcional)
            try:
                subprocess.run(['systemctl', 'start', 'bitcoin-mining-python.service'], 
                             check=True)
                print("✅ Serviço Python iniciado")
            except subprocess.CalledProcessError:
                print("⚠️ Serviço Python não iniciado")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao iniciar serviços: {e}")
            return False
    
    def cleanup_update_files(self):
        """Limpar arquivos de atualização"""
        try:
            print("Limpando arquivos de atualização...")
            
            if self.update_path.exists():
                # Manter apenas os últimos backups
                update_files = list(self.update_path.glob("bitcoin_mining_automation_*.tar.gz"))
                update_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                
                for old_file in update_files[self.keep_backups:]:
                    old_file.unlink()
                    print(f"✅ Removido: {old_file.name}")
                
                # Remover diretórios extraídos
                for extract_dir in self.update_path.glob("extracted_*"):
                    shutil.rmtree(extract_dir)
                    print(f"✅ Removido: {extract_dir.name}")
            
        except Exception as e:
            print(f"⚠️ Erro ao limpar arquivos: {e}")
    
    def run_update(self, target_version: Optional[str] = None) -> bool:
        """Executar atualização"""
        try:
            print("Iniciando atualização do sistema...")
            print(f"Diretório base: {self.base_path}")
            print()
            
            # Verificar requisitos
            if not self.check_system_requirements():
                return False
            
            # Obter versão atual
            current_version = self.get_current_version()
            print(f"Versão atual: {current_version}")
            
            # Obter versão alvo
            if target_version:
                latest_version = target_version
            else:
                latest_version = self.get_latest_version()
                if not latest_version:
                    return False
            
            # Verificar se precisa atualizar
            if current_version == latest_version:
                print(f"✅ Sistema já está na versão mais recente: {latest_version}")
                return True
            
            print(f"Atualizando de {current_version} para {latest_version}")
            print()
            
            # Fazer backup
            if not self.backup_current_system():
                print("❌ Falha no backup. Abortando atualização.")
                return False
            
            # Parar serviços
            if not self.stop_services():
                print("❌ Falha ao parar serviços. Abortando atualização.")
                return False
            
            # Baixar atualização
            update_file = self.download_update(latest_version)
            if not update_file:
                print("❌ Falha ao baixar atualização. Abortando.")
                return False
            
            # Extrair atualização
            source_dir = self.extract_update(update_file)
            if not source_dir:
                print("❌ Falha ao extrair atualização. Abortando.")
                return False
            
            # Atualizar arquivos
            if not self.update_files(source_dir):
                print("❌ Falha ao atualizar arquivos. Abortando.")
                return False
            
            # Atualizar dependências
            if not self.update_dependencies():
                print("❌ Falha ao atualizar dependências. Abortando.")
                return False
            
            # Atualizar versão
            if not self.update_version_file(latest_version):
                print("❌ Falha ao atualizar versão. Abortando.")
                return False
            
            # Iniciar serviços
            if not self.start_services():
                print("❌ Falha ao iniciar serviços.")
                return False
            
            # Limpar arquivos
            self.cleanup_update_files()
            
            print()
            print("✅ Atualização concluída com sucesso!")
            print(f"✅ Versão: {latest_version}")
            print("✅ Serviços iniciados")
            print()
            print("Próximos passos:")
            print("1. Verificar status: ./status.sh")
            print("2. Verificar logs: tail -f logs/bitcoin_mining.log")
            print("3. Acessar interface: http://localhost:8000")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro durante a atualização: {e}")
            return False

def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Atualizador do Sistema de Mineração - Raspberry Pi')
    parser.add_argument('--version', '-v', type=str, 
                       help='Versão específica para atualizar')
    parser.add_argument('--no-backup', action='store_true', 
                       help='Não fazer backup antes da atualização')
    parser.add_argument('--no-restart', action='store_true', 
                       help='Não reiniciar serviços após a atualização')
    parser.add_argument('--check-only', action='store_true', 
                       help='Apenas verificar se há atualizações disponíveis')
    
    args = parser.parse_args()
    
    print("Atualizador do Sistema de Mineração - Raspberry Pi")
    print("Sistema de Automação para Mineração de Bitcoin")
    print("=" * 50)
    
    # Verificar se está rodando como root
    if os.geteuid() != 0:
        print("❌ Este script deve ser executado como root (sudo)")
        sys.exit(1)
    
    # Verificar se está no diretório correto
    if not Path("/opt/bitcoin_mining").exists():
        print("❌ Diretório /opt/bitcoin_mining não encontrado")
        print("Execute primeiro o script de instalação")
        sys.exit(1)
    
    # Executar atualização
    updater = RaspberryPiUpdater()
    
    # Configurar opções
    updater.auto_backup = not args.no_backup
    updater.auto_restart = not args.no_restart
    
    if args.check_only:
        # Apenas verificar versão
        current_version = updater.get_current_version()
        latest_version = updater.get_latest_version()
        
        print(f"Versão atual: {current_version}")
        print(f"Versão mais recente: {latest_version}")
        
        if current_version == latest_version:
            print("✅ Sistema está atualizado")
        else:
            print("⚠️ Atualização disponível")
    else:
        # Executar atualização
        success = updater.run_update(args.version)
        
        if success:
            print("\n🎉 Atualização concluída com sucesso!")
        else:
            print("\n❌ Falha na atualização")
            sys.exit(1)

if __name__ == "__main__":
    main()


