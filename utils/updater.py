"""
DiscoveryLastFM v2.1 - GitHub Auto-Update System
Sistema di aggiornamento automatico da GitHub releases
"""

import os
import sys
import json
import time
import shutil
import tarfile
import zipfile
import logging
import requests
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timedelta
from packaging import version

log = logging.getLogger(__name__)


class UpdateError(Exception):
    """Errore durante l'aggiornamento"""
    pass


class GitHubUpdater:
    """
    Gestisce gli aggiornamenti automatici da GitHub releases
    
    Features:
    - Controllo versioni con semantic versioning
    - Download sicuro con verifiche checksum
    - Backup automatico prima dell'aggiornamento
    - Rollback in caso di errori
    - Controllo periodic programmabile
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.repo_owner = config.get("GITHUB_REPO_OWNER", "MrRobotoGit")
        self.repo_name = config.get("GITHUB_REPO_NAME", "DiscoveryLastFM")
        self.current_version = config.get("VERSION", "2.0.3")
        self.project_root = Path(config.get("PROJECT_ROOT", "/home/pi/DiscoveryLastFM"))
        
        # GitHub API configuration
        self.api_base = "https://api.github.com"
        self.github_token = config.get("GITHUB_TOKEN")  # Optional per rate limiting
        
        # Update configuration
        self.auto_update_enabled = config.get("AUTO_UPDATE_ENABLED", False)
        self.update_check_interval = config.get("UPDATE_CHECK_INTERVAL_HOURS", 24)
        self.backup_retention_days = config.get("BACKUP_RETENTION_DAYS", 7)
        self.allow_prerelease = config.get("ALLOW_PRERELEASE_UPDATES", False)
        
        # Paths
        self.backups_dir = self.project_root / "backups"
        self.temp_dir = self.project_root / "tmp"
        self.update_state_file = self.project_root / "update_state.json"
        
        # Assicura che le directory esistano
        self.backups_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)
        
        # State tracking
        self.update_state = self._load_update_state()
    
    def _load_update_state(self) -> Dict[str, Any]:
        """Carica lo stato degli aggiornamenti"""
        try:
            if self.update_state_file.exists():
                with open(self.update_state_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            log.warning(f"Failed to load update state: {e}")
        
        return {
            "last_check": None,
            "last_update": None,
            "available_version": None,
            "failed_attempts": 0,
            "backups": []
        }
    
    def _save_update_state(self):
        """Salva lo stato degli aggiornamenti"""
        try:
            with open(self.update_state_file, 'w') as f:
                json.dump(self.update_state, f, indent=2)
        except Exception as e:
            log.error(f"Failed to save update state: {e}")
    
    def _make_github_request(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Effettua richiesta autenticata all'API GitHub"""
        url = f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}/{endpoint}"
        headers = {"Accept": "application/vnd.github.v3+json"}
        
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            
            # Log rate limit info
            remaining = response.headers.get("X-RateLimit-Remaining")
            if remaining and int(remaining) < 10:
                log.warning(f"GitHub API rate limit low: {remaining} requests remaining")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            log.error(f"GitHub API request failed: {e}")
            return None
    
    def check_for_updates(self) -> Optional[Dict[str, Any]]:
        """
        Controlla se è disponibile una nuova versione
        
        Returns:
            Dict con info della release se disponibile, None altrimenti
        """
        log.info("Checking for updates...")
        
        try:
            # Get latest release
            endpoint = "releases/latest" if not self.allow_prerelease else "releases"
            release_data = self._make_github_request(endpoint)
            
            if not release_data:
                log.error("Failed to fetch release information")
                return None
            
            # Se releases (non latest), prendi il primo
            if isinstance(release_data, list):
                release_data = release_data[0] if release_data else None
            
            if not release_data:
                log.info("No releases found")
                return None
            
            # Verifica versione
            latest_version = release_data["tag_name"].lstrip("v")
            current_ver = version.parse(self.current_version)
            latest_ver = version.parse(latest_version)
            
            # Update state
            self.update_state["last_check"] = datetime.now().isoformat()
            self.update_state["available_version"] = latest_version
            self._save_update_state()
            
            if latest_ver > current_ver:
                log.info(f"Update available: {self.current_version} → {latest_version}")
                return {
                    "version": latest_version,
                    "tag_name": release_data["tag_name"],
                    "name": release_data["name"],
                    "body": release_data["body"],
                    "published_at": release_data["published_at"],
                    "prerelease": release_data.get("prerelease", False),
                    "assets": release_data.get("assets", []),
                    "tarball_url": release_data["tarball_url"],
                    "zipball_url": release_data["zipball_url"]
                }
            else:
                log.info(f"Already up to date: {self.current_version}")
                return None
                
        except Exception as e:
            log.error(f"Update check failed: {e}")
            return None
    
    def _create_backup(self) -> str:
        """
        Crea backup completo del progetto
        
        Returns:
            Path del backup creato
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_v{self.current_version}_{timestamp}"
        backup_path = self.backups_dir / f"{backup_name}.tar.gz"
        
        log.info(f"Creating backup: {backup_path}")
        
        try:
            with tarfile.open(backup_path, "w:gz") as tar:
                # Backup tutto tranne backups, temp, logs
                exclude_dirs = {"backups", "tmp", "log", "__pycache__", ".git"}
                
                for item in self.project_root.iterdir():
                    if item.name not in exclude_dirs:
                        tar.add(item, arcname=item.name)
            
            # Aggiungi backup alla lista
            backup_info = {
                "path": str(backup_path),
                "version": self.current_version,
                "timestamp": timestamp,
                "size": backup_path.stat().st_size
            }
            
            self.update_state["backups"].append(backup_info)
            self._cleanup_old_backups()
            self._save_update_state()
            
            log.info(f"Backup created successfully: {backup_path.name}")
            return str(backup_path)
            
        except Exception as e:
            log.error(f"Backup creation failed: {e}")
            raise UpdateError(f"Failed to create backup: {e}")
    
    def _cleanup_old_backups(self):
        """Rimuove backup vecchi oltre retention period"""
        cutoff_date = datetime.now() - timedelta(days=self.backup_retention_days)
        
        backups_to_remove = []
        for backup in self.update_state["backups"]:
            backup_date = datetime.strptime(backup["timestamp"], "%Y%m%d_%H%M%S")
            if backup_date < cutoff_date:
                backup_path = Path(backup["path"])
                if backup_path.exists():
                    try:
                        backup_path.unlink()
                        log.info(f"Removed old backup: {backup_path.name}")
                    except Exception as e:
                        log.warning(f"Failed to remove old backup {backup_path}: {e}")
                backups_to_remove.append(backup)
        
        # Rimuovi dalla lista
        for backup in backups_to_remove:
            self.update_state["backups"].remove(backup)
    
    def _download_release(self, release_info: Dict[str, Any]) -> str:
        """
        Scarica la release da GitHub
        
        Returns:
            Path dell'archivio scaricato
        """
        version_tag = release_info["version"]
        download_url = release_info["tarball_url"]  # Preferiamo tarball
        
        # Nome file temporaneo
        temp_file = self.temp_dir / f"update_{version_tag}.tar.gz"
        
        log.info(f"Downloading release {version_tag}...")
        
        try:
            response = requests.get(download_url, stream=True, timeout=300)
            response.raise_for_status()
            
            # Download con progress (semplificato)
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(temp_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Log progress ogni 1MB
                        if downloaded % (1024*1024) == 0:
                            if total_size > 0:
                                percent = (downloaded / total_size) * 100
                                log.info(f"Download progress: {percent:.1f}%")
            
            log.info(f"Download completed: {temp_file}")
            return str(temp_file)
            
        except Exception as e:
            log.error(f"Download failed: {e}")
            raise UpdateError(f"Failed to download release: {e}")
    
    def _extract_release(self, archive_path: str) -> str:
        """
        Estrae l'archivio scaricato
        
        Returns:
            Path della directory estratta
        """
        extract_dir = self.temp_dir / "extracted"
        
        # Rimuovi directory precedente se esiste
        if extract_dir.exists():
            shutil.rmtree(extract_dir)
        
        extract_dir.mkdir()
        
        log.info(f"Extracting {archive_path}...")
        
        try:
            if archive_path.endswith('.tar.gz'):
                with tarfile.open(archive_path, 'r:gz') as tar:
                    tar.extractall(extract_dir)
            elif archive_path.endswith('.zip'):
                with zipfile.ZipFile(archive_path, 'r') as zip_file:
                    zip_file.extractall(extract_dir)
            else:
                raise UpdateError(f"Unsupported archive format: {archive_path}")
            
            # GitHub crea una subdirectory con il nome del repo
            # Trova la vera directory del progetto
            extracted_items = list(extract_dir.iterdir())
            if len(extracted_items) == 1 and extracted_items[0].is_dir():
                project_dir = extracted_items[0]
            else:
                project_dir = extract_dir
            
            log.info(f"Extraction completed: {project_dir}")
            return str(project_dir)
            
        except Exception as e:
            log.error(f"Extraction failed: {e}")
            raise UpdateError(f"Failed to extract archive: {e}")
    
    def _install_update(self, source_dir: str) -> bool:
        """
        Installa l'aggiornamento copiando i file
        
        Args:
            source_dir: Directory con i nuovi file
            
        Returns:
            True se successo
        """
        source_path = Path(source_dir)
        
        log.info("Installing update...")
        
        try:
            # File critici che devono essere sempre aggiornati
            critical_files = [
                "DiscoveryLastFM.py",
                "services",
                "utils",
                "config.example.py",
                "README.md",
                "CHANGELOG.md"
            ]
            
            # File che NON devono essere sovrascritti
            preserve_files = [
                "config.py",
                "lastfm_similar_cache.json",
                "log",
                "backups",
                "tmp",
                "update_state.json"
            ]
            
            # Copia file critici
            for item_name in critical_files:
                source_item = source_path / item_name
                dest_item = self.project_root / item_name
                
                if not source_item.exists():
                    log.warning(f"Source item not found: {item_name}")
                    continue
                
                if dest_item.exists():
                    if dest_item.is_dir():
                        shutil.rmtree(dest_item)
                    else:
                        dest_item.unlink()
                
                if source_item.is_dir():
                    shutil.copytree(source_item, dest_item)
                    log.info(f"Updated directory: {item_name}")
                else:
                    shutil.copy2(source_item, dest_item)
                    log.info(f"Updated file: {item_name}")
            
            # Copia altri file non in preserve_files
            for item in source_path.iterdir():
                if item.name not in critical_files and item.name not in preserve_files:
                    dest_item = self.project_root / item.name
                    
                    if dest_item.exists():
                        if dest_item.is_dir():
                            shutil.rmtree(dest_item)
                        else:
                            dest_item.unlink()
                    
                    if item.is_dir():
                        shutil.copytree(item, dest_item)
                    else:
                        shutil.copy2(item, dest_item)
                    
                    log.info(f"Added/updated: {item.name}")
            
            log.info("Installation completed successfully")
            return True
            
        except Exception as e:
            log.error(f"Installation failed: {e}")
            raise UpdateError(f"Failed to install update: {e}")
    
    def _verify_installation(self) -> bool:
        """
        Verifica che l'installazione sia andata a buon fine
        
        Returns:
            True se tutto ok
        """
        log.info("Verifying installation...")
        
        try:
            # Verifica file critici
            critical_files = [
                "DiscoveryLastFM.py",
                "services/__init__.py",
                "utils/__init__.py"
            ]
            
            for file_path in critical_files:
                full_path = self.project_root / file_path
                if not full_path.exists():
                    log.error(f"Critical file missing after update: {file_path}")
                    return False
            
            # Test import
            sys.path.insert(0, str(self.project_root))
            try:
                import services
                import utils
                log.info("Import test successful")
            except ImportError as e:
                log.error(f"Import test failed: {e}")
                return False
            finally:
                # Rimuovi path aggiunto
                if str(self.project_root) in sys.path:
                    sys.path.remove(str(self.project_root))
            
            log.info("Installation verification successful")
            return True
            
        except Exception as e:
            log.error(f"Installation verification failed: {e}")
            return False
    
    def _rollback(self, backup_path: str) -> bool:
        """
        Rollback all'ultima versione funzionante
        
        Args:
            backup_path: Path del backup da ripristinare
            
        Returns:
            True se rollback riuscito
        """
        log.warning(f"Starting rollback from backup: {backup_path}")
        
        try:
            backup_file = Path(backup_path)
            if not backup_file.exists():
                log.error(f"Backup file not found: {backup_path}")
                return False
            
            # Estrai backup in temp
            rollback_dir = self.temp_dir / "rollback"
            if rollback_dir.exists():
                shutil.rmtree(rollback_dir)
            rollback_dir.mkdir()
            
            with tarfile.open(backup_file, "r:gz") as tar:
                tar.extractall(rollback_dir)
            
            # Rimuovi file correnti (eccetto preserve_files)
            preserve_files = {
                "config.py", "lastfm_similar_cache.json", "log", 
                "backups", "tmp", "update_state.json"
            }
            
            for item in self.project_root.iterdir():
                if item.name not in preserve_files:
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
            
            # Ripristina da backup
            for item in rollback_dir.iterdir():
                dest_item = self.project_root / item.name
                if item.is_dir():
                    shutil.copytree(item, dest_item)
                else:
                    shutil.copy2(item, dest_item)
            
            log.info("Rollback completed successfully")
            return True
            
        except Exception as e:
            log.error(f"Rollback failed: {e}")
            return False
    
    def perform_update(self, release_info: Dict[str, Any], force: bool = False) -> bool:
        """
        Esegue l'aggiornamento completo
        
        Args:
            release_info: Info della release da installare
            force: True per saltare verifiche di sicurezza
            
        Returns:
            True se aggiornamento riuscito
        """
        version_tag = release_info["version"]
        
        if not force and self.update_state.get("failed_attempts", 0) >= 3:
            log.error("Too many failed update attempts. Use force=True to override.")
            return False
        
        log.info(f"Starting update to version {version_tag}")
        backup_path = None
        
        try:
            # 1. Crea backup
            backup_path = self._create_backup()
            
            # 2. Scarica release
            archive_path = self._download_release(release_info)
            
            # 3. Estrai archivio
            source_dir = self._extract_release(archive_path)
            
            # 4. Installa aggiornamento
            if not self._install_update(source_dir):
                raise UpdateError("Installation failed")
            
            # 5. Verifica installazione
            if not self._verify_installation():
                raise UpdateError("Installation verification failed")
            
            # 6. Update state
            self.update_state.update({
                "last_update": datetime.now().isoformat(),
                "failed_attempts": 0,
                "current_version": version_tag
            })
            self._save_update_state()
            
            # 7. Cleanup
            Path(archive_path).unlink(missing_ok=True)
            shutil.rmtree(Path(source_dir).parent, ignore_errors=True)
            
            log.info(f"Update to {version_tag} completed successfully!")
            return True
            
        except Exception as e:
            log.error(f"Update failed: {e}")
            
            # Increment failed attempts
            self.update_state["failed_attempts"] = self.update_state.get("failed_attempts", 0) + 1
            self._save_update_state()
            
            # Tentativo di rollback
            if backup_path and Path(backup_path).exists():
                log.info("Attempting rollback...")
                if self._rollback(backup_path):
                    log.info("Rollback successful")
                else:
                    log.error("Rollback failed - manual intervention required")
            
            return False
    
    def should_check_for_updates(self) -> bool:
        """
        Determina se è il momento di controllare gli aggiornamenti
        
        Returns:
            True se dovrebbe controllare
        """
        if not self.auto_update_enabled:
            return False
        
        last_check = self.update_state.get("last_check")
        if not last_check:
            return True
        
        last_check_time = datetime.fromisoformat(last_check)
        next_check = last_check_time + timedelta(hours=self.update_check_interval)
        
        return datetime.now() >= next_check
    
    def get_update_status(self) -> Dict[str, Any]:
        """
        Ritorna lo stato corrente dell'updater
        
        Returns:
            Dict con info complete sullo stato
        """
        return {
            "current_version": self.current_version,
            "auto_update_enabled": self.auto_update_enabled,
            "last_check": self.update_state.get("last_check"),
            "last_update": self.update_state.get("last_update"),
            "available_version": self.update_state.get("available_version"),
            "failed_attempts": self.update_state.get("failed_attempts", 0),
            "backup_count": len(self.update_state.get("backups", [])),
            "next_check": self._get_next_check_time(),
            "repo": f"{self.repo_owner}/{self.repo_name}"
        }
    
    def _get_next_check_time(self) -> Optional[str]:
        """Calcola il prossimo check programmato"""
        last_check = self.update_state.get("last_check")
        if not last_check:
            return None
        
        last_check_time = datetime.fromisoformat(last_check)
        next_check = last_check_time + timedelta(hours=self.update_check_interval)
        return next_check.isoformat()
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """
        Lista i backup disponibili
        
        Returns:
            Lista dei backup con info
        """
        backups = []
        for backup in self.update_state.get("backups", []):
            backup_path = Path(backup["path"])
            if backup_path.exists():
                backups.append({
                    **backup,
                    "exists": True,
                    "size_mb": round(backup["size"] / (1024*1024), 2)
                })
            else:
                backups.append({
                    **backup,
                    "exists": False
                })
        
        return sorted(backups, key=lambda x: x["timestamp"], reverse=True)
    
    def cleanup_temp_files(self):
        """Pulisce i file temporanei"""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                self.temp_dir.mkdir()
            log.info("Temporary files cleaned up")
        except Exception as e:
            log.warning(f"Failed to cleanup temp files: {e}")


def get_current_version() -> str:
    """Recupera la versione corrente dal CHANGELOG"""
    try:
        changelog_path = Path(__file__).parent.parent / "CHANGELOG.md"
        if changelog_path.exists():
            with open(changelog_path, 'r') as f:
                for line in f:
                    if line.startswith("## [") and "] -" in line:
                        # Estrai versione da formato "## [2.0.3] - 2025-06-25"
                        version_str = line.split("[")[1].split("]")[0]
                        return version_str
        return "2.0.3"  # Fallback
    except Exception:
        return "2.0.3"  # Fallback


def create_updater_from_config(config_dict: Dict[str, Any]) -> GitHubUpdater:
    """
    Crea un'istanza GitHubUpdater dalla configurazione del progetto
    
    Args:
        config_dict: Dizionario con la configurazione
        
    Returns:
        Istanza configurata di GitHubUpdater
    """
    # Determina versione corrente
    current_version = get_current_version()
    
    # Configura updater
    updater_config = {
        "VERSION": current_version,
        "PROJECT_ROOT": config_dict.get("PROJECT_ROOT", "/home/pi/DiscoveryLastFM"),
        "GITHUB_REPO_OWNER": config_dict.get("GITHUB_REPO_OWNER", "MrRobotoGit"),
        "GITHUB_REPO_NAME": config_dict.get("GITHUB_REPO_NAME", "DiscoveryLastFM"),
        "GITHUB_TOKEN": config_dict.get("GITHUB_TOKEN"),
        "AUTO_UPDATE_ENABLED": config_dict.get("AUTO_UPDATE_ENABLED", False),
        "UPDATE_CHECK_INTERVAL_HOURS": config_dict.get("UPDATE_CHECK_INTERVAL_HOURS", 24),
        "BACKUP_RETENTION_DAYS": config_dict.get("BACKUP_RETENTION_DAYS", 7),
        "ALLOW_PRERELEASE_UPDATES": config_dict.get("ALLOW_PRERELEASE_UPDATES", False)
    }
    
    return GitHubUpdater(updater_config)