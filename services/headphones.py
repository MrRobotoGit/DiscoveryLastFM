"""
DiscoveryLastFM v2.0 - Headphones Service
Wrapper per API Headphones esistenti con retry logic identico
"""

import logging
import time
import urllib.parse
import requests
from typing import Dict, Any, Optional

from .base import MusicServiceBase, ArtistInfo, AlbumInfo
from .exceptions import ServiceError, ConfigurationError, ConnectionError

log = logging.getLogger(__name__)


class HeadphonesService(MusicServiceBase):
    """Wrapper per API Headphones esistenti"""
    
    def _validate_config(self) -> None:
        """Validazione configurazione Headphones"""
        required = ["HP_API_KEY", "HP_ENDPOINT"]
        missing = [k for k in required if not self.config.get(k)]
        if missing:
            raise ConfigurationError(f"Missing HP config: {missing}", missing)
    
    def _hp_request(self, cmd: str, **params) -> Any:
        """
        Estrae e mantiene IDENTICA la logica hp_api esistente
        Preserva timeout, retry, error handling originali
        """
        base = self.config["HP_ENDPOINT"].rstrip("/") + "/api"
        params.update({"cmd": cmd, "apikey": self.config["HP_API_KEY"]})
        
        # Eredita configurazione retry da main - IDENTICA
        max_retries = self.config.get("HP_MAX_RETRIES", 3)
        retry_delay = self.config.get("HP_RETRY_DELAY", 5)
        
        # Timeout personalizzati per comando - IDENTICI all'originale
        timeout_map = {
            "forceSearch": 300,
            "addAlbum": 120, 
            "queueAlbum": 120,
            "addArtist": 120
        }
        timeout = timeout_map.get(cmd, 60)
        
        # Implementa retry logic IDENTICA al main script
        for attempt in range(max_retries):
            try:
                if self.config.get("DEBUG_PRINT", False):
                    print(f"[DEBUG] HP  → {base}?{urllib.parse.urlencode(params)} (tentativo {attempt+1}/{max_retries})")
                
                response = requests.get(base, params=params, timeout=timeout)
                
                if self.config.get("DEBUG_PRINT", False):
                    print(f"[DEBUG] HP  ← {response.status_code}")
                
                # Gestione errori 500 specifici con retry - IDENTICA
                if response.status_code == 500 and cmd == "queueAlbum":
                    log.warning(f"Errore 500 per queueAlbum, tentativo {attempt+1}/{max_retries}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (attempt + 1))
                        continue
                
                response.raise_for_status()
                ct = response.headers.get("Content-Type", "")
                return response.json() if ct.startswith("application/json") else response.text
                
            except requests.exceptions.Timeout:
                log.warning(f"Timeout per {cmd}, tentativo {attempt+1}/{max_retries}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                raise ServiceError(f"HP timeout for {cmd}", "headphones")
                
            except Exception as e:
                log.warning(f"Headphones {cmd} fallito: {e}, tentativo {attempt+1}/{max_retries}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                raise ServiceError(f"HP error for {cmd}: {e}", "headphones", e)
        
        return None
    
    def test_connection(self) -> bool:
        """Test connettività Headphones"""
        try:
            result = self._hp_request("getIndex")
            return result is not None
        except Exception as e:
            log.error(f"HP connection test failed: {e}")
            return False
    
    def add_artist(self, artist_info: ArtistInfo) -> bool:
        """Aggiunge artista a Headphones"""
        try:
            result = self._hp_request("addArtist", id=artist_info.mbid)
            return result is not None
        except Exception as e:
            log.error(f"HP add_artist failed for {artist_info.name}: {e}")
            return False
    
    def get_artist(self, mbid: str) -> Optional[ArtistInfo]:
        """Recupera info artista da Headphones"""
        try:
            result = self._hp_request("getArtist", id=mbid)
            if result and isinstance(result, dict):
                artist_data = result.get("artist", [])
                if artist_data:
                    return ArtistInfo(
                        mbid=mbid,
                        name=artist_data.get("ArtistName", ""),
                        service_id=artist_data.get("ArtistID"),
                        monitored=artist_data.get("Status") == "Active"
                    )
            return None
        except Exception as e:
            log.error(f"HP get_artist failed for {mbid}: {e}")
            return None
    
    def refresh_artist(self, mbid: str) -> bool:
        """Aggiorna metadati artista in Headphones"""
        try:
            result = self._hp_request("refreshArtist", id=mbid)
            return result is not None
        except Exception as e:
            log.error(f"HP refresh_artist failed for {mbid}: {e}")
            return False
    
    def add_album(self, album_info: AlbumInfo) -> bool:
        """Aggiunge album a Headphones"""
        try:
            result = self._hp_request("addAlbum", id=album_info.mbid)
            return result is not None
        except Exception as e:
            log.error(f"HP add_album failed for {album_info.title}: {e}")
            return False
    
    def queue_album(self, album_info: AlbumInfo, force_new: bool = False) -> bool:
        """Accoda album per download in Headphones"""
        try:
            result = self._hp_request("queueAlbum", id=album_info.mbid, new=force_new)
            return result is not None
        except Exception as e:
            log.error(f"HP queue_album failed for {album_info.title}: {e}")
            return False
    
    def force_search(self) -> bool:
        """Forza ricerca generale in Headphones"""
        try:
            result = self._hp_request("forceSearch")
            return result is not None
        except Exception as e:
            log.error(f"HP force_search failed: {e}")
            return False
    
    def get_service_info(self) -> Dict[str, Any]:
        """Info servizio per diagnostica"""
        try:
            # Prova a ottenere info di versione da Headphones
            status = self._hp_request("getIndex")
            return {
                "service": "headphones",
                "endpoint": self.config["HP_ENDPOINT"],
                "status": "connected" if status else "error"
            }
        except Exception:
            return {
                "service": "headphones", 
                "endpoint": self.config["HP_ENDPOINT"],
                "status": "error"
            }
    
    def album_exists(self, mbid: str, added_albums: set) -> bool:
        """
        Verifica se un album esiste già in Headphones
        Mantiene IDENTICA la logica originale
        """
        if mbid in added_albums:
            return True
            
        try:
            response = self._hp_request("getAlbum", id=mbid)
            if not response or not isinstance(response, dict):
                return False
                
            # Un album non esistente restituisce array vuoti
            album = response.get("album", [])
            tracks = response.get("tracks", [])
            
            # Se entrambi gli array sono vuoti, l'album non esiste
            if not album and not tracks:
                if self.config.get("DEBUG_PRINT", False):
                    print(f"[DEBUG] Album {mbid} non trovato in Headphones")
                return False
                
            # Se abbiamo dati in uno dei due array, l'album esiste
            return True
            
        except Exception as e:
            log.error(f"HP album_exists failed for {mbid}: {e}")
            return False
    
    @classmethod
    def get_config_requirements(cls) -> Dict[str, Any]:
        """Requisiti di configurazione per Headphones"""
        return {
            "required": ["HP_API_KEY", "HP_ENDPOINT"],
            "optional": {
                "HP_MAX_RETRIES": {"default": 3, "type": "int"},
                "HP_RETRY_DELAY": {"default": 5, "type": "int"},
                "HP_TIMEOUT": {"default": 60, "type": "int"},
                "DEBUG_PRINT": {"default": False, "type": "bool"}
            }
        }