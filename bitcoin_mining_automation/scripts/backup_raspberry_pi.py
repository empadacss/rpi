#!/usr/bin/env python3
"""
Script de backup específico para Raspberry Pi
Sistema de Automação para Mineração de Bitcoin
"""

import os
import sys
import json
import shutil
import tarfile
import gzip
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

class RaspberryPiBackup:
    """Classe para backup do sistema no Raspberry Pi"""
    
    def __init__(self):
        self.base_path = Path("/opt/bitcoin_mining")
        self.backup_path = self.base_path / "backup"
        self.data_path = self.base_path / "data"
        self.logs_path = self.base_path / "logs"
        self.config_path = self.base_path / "config"
        self.reports_path = self.base_path / "reports"
        
        # Configurações de backup
        self.max_backups = 7  # Manter apenas os últimos 7 backups
        self.compression_level = 6  # Nível de compressão (1-9)
        
    def create_backup_directories(self):
        """Criar diretórios de backup"""
        try:
            self.backup_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Diretório de backup: {self.backup_path}")
            return True
        except Exception as e:
            print(f"❌ Erro ao criar diretório de backup: {e}")
            return False
    
    def get_backup_info(self) -> Dict[str, Any]:
        """Obter informações do backup"""
        return {
            "timestamp": datetime.now().isoformat(),
            "hostname": os.uname().nodename,
            "platform": os.uname().sysname,
            "architecture": os.uname().machine,
            "backup_version": "1.0.0",
            "backup_type": "full"
        }
    
    def backup_database(self, backup_dir: Path) -> bool:
        """Fazer backup do banco de dados"""
        try:
            print("Fazendo backup do banco de dados...")
            
            # Verificar se existe banco SQLite
            sqlite_files = list(self.data_path.glob("*.db"))
            if sqlite_files:
                for db_file in sqlite_files:
                    backup_file = backup_dir / f"database_{db_file.name}"
                    shutil.copy2(db_file, backup_file)
                    print(f"✅ Banco SQLite: {db_file.name}")
            
            # Verificar se existe PostgreSQL (via Docker)
            try:
                import subprocess
                result = subprocess.run(['docker', 'exec', 'bitcoin_mining_postgres', 
                                       'pg_dump', '-U', 'bitcoin_mining', 'bitcoin_mining'], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    pg_backup_file = backup_dir / "postgresql_backup.sql"
                    with open(pg_backup_file, 'w') as f:
                        f.write(result.stdout)
                    print("✅ Banco PostgreSQL")
                else:
                    print("⚠️ PostgreSQL não disponível")
                    
            except Exception as e:
                print(f"⚠️ Erro ao fazer backup do PostgreSQL: {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao fazer backup do banco de dados: {e}")
            return False
    
    def backup_configuration(self, backup_dir: Path) -> bool:
        """Fazer backup das configurações"""
        try:
            print("Fazendo backup das configurações...")
            
            config_backup_dir = backup_dir / "config"
            config_backup_dir.mkdir(exist_ok=True)
            
            # Copiar arquivos de configuração
            config_files = [
                ".env",
                "config/devices.yaml",
                "config/automation.yaml",
                "config/logging.yaml",
                "docker-compose.yml",
                "requirements.txt"
            ]
            
            for config_file in config_files:
                source_file = self.base_path / config_file
                if source_file.exists():
                    dest_file = config_backup_dir / config_file
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_file, dest_file)
                    print(f"✅ {config_file}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao fazer backup das configurações: {e}")
            return False
    
    def backup_data(self, backup_dir: Path) -> bool:
        """Fazer backup dos dados"""
        try:
            print("Fazendo backup dos dados...")
            
            data_backup_dir = backup_dir / "data"
            data_backup_dir.mkdir(exist_ok=True)
            
            # Copiar diretórios de dados
            data_dirs = [
                "inverter",
                "multimedidor", 
                "f2pool",
                "environmental",
                "asic",
                "reports"
            ]
            
            for data_dir in data_dirs:
                source_dir = self.data_path / data_dir
                if source_dir.exists():
                    dest_dir = data_backup_dir / data_dir
                    shutil.copytree(source_dir, dest_dir, dirs_exist_ok=True)
                    print(f"✅ {data_dir}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao fazer backup dos dados: {e}")
            return False
    
    def backup_logs(self, backup_dir: Path) -> bool:
        """Fazer backup dos logs"""
        try:
            print("Fazendo backup dos logs...")
            
            logs_backup_dir = backup_dir / "logs"
            logs_backup_dir.mkdir(exist_ok=True)
            
            # Copiar logs recentes (últimos 7 dias)
            cutoff_date = datetime.now() - timedelta(days=7)
            
            for log_file in self.logs_path.glob("*.log"):
                if datetime.fromtimestamp(log_file.stat().st_mtime) > cutoff_date:
                    dest_file = logs_backup_dir / log_file.name
                    shutil.copy2(log_file, dest_file)
                    print(f"✅ {log_file.name}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao fazer backup dos logs: {e}")
            return False
    
    def backup_reports(self, backup_dir: Path) -> bool:
        """Fazer backup dos relatórios"""
        try:
            print("Fazendo backup dos relatórios...")
            
            reports_backup_dir = backup_dir / "reports"
            reports_backup_dir.mkdir(exist_ok=True)
            
            # Copiar relatórios recentes (últimos 30 dias)
            cutoff_date = datetime.now() - timedelta(days=30)
            
            for report_file in self.reports_path.glob("*"):
                if report_file.is_file():
                    if datetime.fromtimestamp(report_file.stat().st_mtime) > cutoff_date:
                        dest_file = reports_backup_dir / report_file.name
                        shutil.copy2(report_file, dest_file)
                        print(f"✅ {report_file.name}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao fazer backup dos relatórios: {e}")
            return False
    
    def backup_scripts(self, backup_dir: Path) -> bool:
        """Fazer backup dos scripts"""
        try:
            print("Fazendo backup dos scripts...")
            
            scripts_backup_dir = backup_dir / "scripts"
            scripts_backup_dir.mkdir(exist_ok=True)
            
            # Copiar scripts
            scripts_dir = self.base_path / "scripts"
            if scripts_dir.exists():
                for script_file in scripts_dir.glob("*.py"):
                    dest_file = scripts_backup_dir / script_file.name
                    shutil.copy2(script_file, dest_file)
                    print(f"✅ {script_file.name}")
            
            # Copiar scripts de shell
            for script_file in self.base_path.glob("*.sh"):
                dest_file = scripts_backup_dir / script_file.name
                shutil.copy2(script_file, dest_file)
                print(f"✅ {script_file.name}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao fazer backup dos scripts: {e}")
            return False
    
    def backup_docker_volumes(self, backup_dir: Path) -> bool:
        """Fazer backup dos volumes Docker"""
        try:
            print("Fazendo backup dos volumes Docker...")
            
            volumes_backup_dir = backup_dir / "docker_volumes"
            volumes_backup_dir.mkdir(exist_ok=True)
            
            # Listar volumes Docker
            try:
                import subprocess
                result = subprocess.run(['docker', 'volume', 'ls', '--format', 'json'], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    volumes = []
                    for line in result.stdout.strip().split('\n'):
                        if line:
                            try:
                                volume = json.loads(line)
                                volumes.append(volume['Name'])
                            except json.JSONDecodeError:
                                continue
                    
                    # Fazer backup dos volumes
                    for volume_name in volumes:
                        if 'bitcoin_mining' in volume_name:
                            volume_backup_file = volumes_backup_dir / f"{volume_name}.tar"
                            
                            # Criar backup do volume
                            result = subprocess.run([
                                'docker', 'run', '--rm', '-v', f'{volume_name}:/volume',
                                '-v', f'{volumes_backup_dir}:/backup',
                                'alpine', 'tar', 'czf', f'/backup/{volume_name}.tar.gz', '-C', '/volume', '.'
                            ], capture_output=True, text=True)
                            
                            if result.returncode == 0:
                                print(f"✅ Volume: {volume_name}")
                            else:
                                print(f"⚠️ Erro no volume: {volume_name}")
                
            except Exception as e:
                print(f"⚠️ Erro ao fazer backup dos volumes Docker: {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao fazer backup dos volumes Docker: {e}")
            return False
    
    def create_backup_manifest(self, backup_dir: Path) -> bool:
        """Criar manifesto do backup"""
        try:
            print("Criando manifesto do backup...")
            
            manifest = {
                "backup_info": self.get_backup_info(),
                "files": [],
                "directories": [],
                "total_size": 0
            }
            
            # Contar arquivos e calcular tamanho
            total_size = 0
            for root, dirs, files in os.walk(backup_dir):
                for file in files:
                    file_path = Path(root) / file
                    file_size = file_path.stat().st_size
                    total_size += file_size
                    
                    manifest["files"].append({
                        "path": str(file_path.relative_to(backup_dir)),
                        "size": file_size,
                        "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                    })
                
                for dir_name in dirs:
                    dir_path = Path(root) / dir_name
                    manifest["directories"].append(str(dir_path.relative_to(backup_dir)))
            
            manifest["total_size"] = total_size
            
            # Salvar manifesto
            manifest_file = backup_dir / "backup_manifest.json"
            with open(manifest_file, 'w') as f:
                json.dump(manifest, f, indent=2, default=str)
            
            print(f"✅ Manifesto: {manifest_file}")
            print(f"✅ Tamanho total: {total_size / (1024*1024):.2f} MB")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao criar manifesto: {e}")
            return False
    
    def compress_backup(self, backup_dir: Path) -> Optional[Path]:
        """Comprimir backup"""
        try:
            print("Comprimindo backup...")
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_path / f"bitcoin_mining_backup_{timestamp}.tar.gz"
            
            with tarfile.open(backup_file, 'w:gz', compresslevel=self.compression_level) as tar:
                tar.add(backup_dir, arcname=backup_dir.name)
            
            # Remover diretório temporário
            shutil.rmtree(backup_dir)
            
            print(f"✅ Backup comprimido: {backup_file}")
            print(f"✅ Tamanho final: {backup_file.stat().st_size / (1024*1024):.2f} MB")
            
            return backup_file
            
        except Exception as e:
            print(f"❌ Erro ao comprimir backup: {e}")
            return None
    
    def cleanup_old_backups(self):
        """Limpar backups antigos"""
        try:
            print("Limpando backups antigos...")
            
            # Listar arquivos de backup
            backup_files = list(self.backup_path.glob("bitcoin_mining_backup_*.tar.gz"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Remover backups antigos
            if len(backup_files) > self.max_backups:
                for old_backup in backup_files[self.max_backups:]:
                    old_backup.unlink()
                    print(f"✅ Removido: {old_backup.name}")
            
            print(f"✅ Mantidos {min(len(backup_files), self.max_backups)} backups")
            
        except Exception as e:
            print(f"❌ Erro ao limpar backups antigos: {e}")
    
    def create_restore_script(self, backup_file: Path):
        """Criar script de restauração"""
        try:
            print("Criando script de restauração...")
            
            restore_script = f"""#!/bin/bash
# Script de restauração do backup
# Backup: {backup_file.name}
# Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

echo "Restaurando backup: {backup_file.name}"

# Verificar se está rodando como root
if [ "$EUID" -ne 0 ]; then
    echo "Por favor, execute como root (sudo ./restore.sh)"
    exit 1
fi

# Parar serviços
echo "Parando serviços..."
systemctl stop bitcoin-mining-python.service
docker-compose down

# Fazer backup do estado atual
echo "Fazendo backup do estado atual..."
cp -r /opt/bitcoin_mining /opt/bitcoin_mining_backup_$(date +%Y%m%d_%H%M%S)

# Extrair backup
echo "Extraindo backup..."
cd /opt/bitcoin_mining
tar -xzf {backup_file}

# Restaurar permissões
echo "Restaurando permissões..."
chown -R root:root /opt/bitcoin_mining
chmod -R 755 /opt/bitcoin_mining

# Restaurar banco de dados
echo "Restaurando banco de dados..."
if [ -f "backup/database_bitcoin_mining.db" ]; then
    cp backup/database_bitcoin_mining.db data/
fi

# Restaurar volumes Docker
echo "Restaurando volumes Docker..."
if [ -d "backup/docker_volumes" ]; then
    for volume_file in backup/docker_volumes/*.tar.gz; do
        if [ -f "$volume_file" ]; then
            volume_name=$(basename "$volume_file" .tar.gz)
            docker volume create "$volume_name"
            docker run --rm -v "$volume_name":/volume -v "$(pwd)/backup/docker_volumes":/backup alpine tar -xzf "/backup/$(basename "$volume_file")" -C /volume
        fi
    done
fi

# Reiniciar serviços
echo "Reiniciando serviços..."
docker-compose up -d
systemctl start bitcoin-mining-python.service

echo "Restauração concluída!"
echo "Verifique o status: ./status.sh"
"""
            
            restore_file = self.backup_path / f"restore_{backup_file.stem}.sh"
            with open(restore_file, 'w') as f:
                f.write(restore_script)
            
            # Tornar executável
            os.chmod(restore_file, 0o755)
            
            print(f"✅ Script de restauração: {restore_file}")
            
        except Exception as e:
            print(f"❌ Erro ao criar script de restauração: {e}")
    
    def run_backup(self) -> bool:
        """Executar backup completo"""
        try:
            print("Iniciando backup do sistema...")
            print(f"Diretório base: {self.base_path}")
            print(f"Diretório de backup: {self.backup_path}")
            print()
            
            # Criar diretórios de backup
            if not self.create_backup_directories():
                return False
            
            # Criar diretório temporário para backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_backup_dir = self.backup_path / f"temp_backup_{timestamp}"
            temp_backup_dir.mkdir(exist_ok=True)
            
            print(f"Diretório temporário: {temp_backup_dir}")
            print()
            
            # Executar backups
            success = True
            
            if not self.backup_database(temp_backup_dir):
                success = False
            
            if not self.backup_configuration(temp_backup_dir):
                success = False
            
            if not self.backup_data(temp_backup_dir):
                success = False
            
            if not self.backup_logs(temp_backup_dir):
                success = False
            
            if not self.backup_reports(temp_backup_dir):
                success = False
            
            if not self.backup_scripts(temp_backup_dir):
                success = False
            
            if not self.backup_docker_volumes(temp_backup_dir):
                success = False
            
            if not self.create_backup_manifest(temp_backup_dir):
                success = False
            
            if not success:
                print("❌ Alguns backups falharam")
                return False
            
            # Comprimir backup
            backup_file = self.compress_backup(temp_backup_dir)
            if not backup_file:
                return False
            
            # Criar script de restauração
            self.create_restore_script(backup_file)
            
            # Limpar backups antigos
            self.cleanup_old_backups()
            
            print()
            print("✅ Backup concluído com sucesso!")
            print(f"✅ Arquivo: {backup_file}")
            print(f"✅ Tamanho: {backup_file.stat().st_size / (1024*1024):.2f} MB")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro durante o backup: {e}")
            return False

def main():
    """Função principal"""
    print("Sistema de Backup - Raspberry Pi")
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
    
    # Executar backup
    backup = RaspberryPiBackup()
    success = backup.run_backup()
    
    if success:
        print("\n🎉 Backup concluído com sucesso!")
        print("Execute o script de restauração se necessário")
    else:
        print("\n❌ Falha no backup")
        sys.exit(1)

if __name__ == "__main__":
    main()


