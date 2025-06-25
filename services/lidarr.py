"""
DiscoveryLastFM v2.1 - Lidarr Service  
Implementazione completa per Lidarr API v1.0+
"""

import logging
import time
import requests
from typing import Dict, Any, Optional

from .base import MusicServiceBase, ArtistInfo, AlbumInfo
from .exceptions import ServiceError, ConfigurationError, ConnectionError, RateLimitError

log = logging.getLogger(__name__)


class LidarrService(MusicServiceBase):
    """Implementazione completa per Lidarr API v1.0+"""
    
    def __init__(self, config):
        super().__init__(config)
        # Performance metrics tracking
        self.operation_stats = {
            "total_requests": 0,
            "total_time": 0,
            "timeouts": 0,
            "errors": 0,
            "slow_operations": 0,
            "server_unavailable_503": 0
        }
    
    def _validate_config(self) -> None:
        """Validazione configurazione Lidarr"""
        required = ["LIDARR_API_KEY", "LIDARR_ENDPOINT", "LIDARR_ROOT_FOLDER"]
        missing = [k for k in required if not self.config.get(k)]
        if missing:
            raise ConfigurationError(f"Missing Lidarr config: {missing}", missing)
        
        # Validazione profile IDs
        self._validate_profiles()
    
    def _validate_profiles(self) -> None:
        """Validazione profile esistenti in Lidarr"""
        # Assicura che operation_stats sia inizializzato prima di usare _lidarr_request
        if not hasattr(self, 'operation_stats'):
            self.operation_stats = {
                "total_requests": 0, "total_time": 0, "timeouts": 0,
                "errors": 0, "slow_operations": 0, "server_unavailable_503": 0
            }
            
        try:
            # Test quality profile
            quality_id = self.config.get("LIDARR_QUALITY_PROFILE_ID", 1)
            profiles = self._lidarr_request("GET", "qualityprofile")
            if profiles and not any(p.get("id") == quality_id for p in profiles):
                log.warning(f"Quality profile {quality_id} not found in Lidarr")
            
            # Test metadata profile
            metadata_id = self.config.get("LIDARR_METADATA_PROFILE_ID", 1)
            metadata_profiles = self._lidarr_request("GET", "metadataprofile")
            if metadata_profiles and not any(p.get("id") == metadata_id for p in metadata_profiles):
                log.warning(f"Metadata profile {metadata_id} not found in Lidarr")
                
        except Exception as e:
            log.warning(f"Profile validation failed (continuing): {e}")
    
    def _lidarr_request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Richiesta unificata con retry logic e timeout differenziati"""
        url = f"{self.config['LIDARR_ENDPOINT'].rstrip('/')}/api/v1/{endpoint.lstrip('/')}"
        headers = {
            "X-Api-Key": self.config["LIDARR_API_KEY"],
            "Content-Type": "application/json"
        }
        
        # Configurazione retry consistente con HP
        max_retries = self.config.get("LIDARR_MAX_RETRIES", 3)
        retry_delay = self.config.get("LIDARR_RETRY_DELAY", 5)
        
        # Timeout differenziati per operazioni diverse
        timeout_map = {
            "artist/lookup": 300,    # Lookup artisti può essere lento
            "album/lookup": 300,     # Lookup album può essere lento  
            "command": 120,          # Command operations
            "system/status": 30,     # Status check veloce
        }
        
        # Determina timeout basato sull'endpoint
        base_timeout = self.config.get("LIDARR_TIMEOUT", 60)
        timeout = timeout_map.get(endpoint, base_timeout)
        
        # Log timeout usato per debugging
        if self.config.get("DEBUG_PRINT", False):
            print(f"[DEBUG] Using timeout {timeout}s for endpoint {endpoint}")
        
        for attempt in range(max_retries):
            try:
                # Performance timing per debugging
                start_time = time.time()
                
                if self.config.get("DEBUG_PRINT", False):
                    print(f"[DEBUG] Lidarr {method} → {url} (attempt {attempt+1}/{max_retries}, timeout={timeout}s)")
                
                response = requests.request(
                    method, url, headers=headers, timeout=timeout, **kwargs
                )
                
                # Log timing e response
                elapsed = time.time() - start_time
                if self.config.get("DEBUG_PRINT", False):
                    print(f"[DEBUG] Lidarr ← {response.status_code} (took {elapsed:.2f}s)")
                
                # Update performance stats
                self.operation_stats["total_requests"] += 1
                self.operation_stats["total_time"] += elapsed
                
                # Se l'operazione riesce dopo problemi 503, resetta il counter (server recovery)
                if self.operation_stats["server_unavailable_503"] > 0:
                    log.info(f"Lidarr server recovered - resetting 503 error count")
                    self.operation_stats["server_unavailable_503"] = 0
                
                # Warning per operazioni lente anche senza DEBUG_PRINT
                if elapsed > 30:
                    self.operation_stats["slow_operations"] += 1
                    log.warning(f"Slow Lidarr operation: {method} {endpoint} took {elapsed:.2f}s")
                
                # Gestione rate limiting Lidarr
                if response.status_code == 429:
                    wait_time = int(response.headers.get("Retry-After", retry_delay * 2))
                    if attempt < max_retries - 1:
                        log.warning(f"Lidarr rate limit, waiting {wait_time}s")
                        time.sleep(wait_time)
                        continue
                    raise RateLimitError(f"Rate limit exceeded", "lidarr", wait_time)
                
                # Gestione specifica errore 503 Service Unavailable  
                if response.status_code == 503:
                    self.operation_stats["errors"] += 1
                    self.operation_stats["server_unavailable_503"] += 1
                    log.warning(f"Lidarr 503 Service Unavailable: {method} {endpoint} after {elapsed:.2f}s (attempt {attempt+1}/{max_retries})")
                    if attempt < max_retries - 1:
                        # Exponential backoff per 503: 15s, 60s, 180s
                        backoff_delays = [15, 60, 180]
                        wait_time = backoff_delays[min(attempt, len(backoff_delays)-1)]
                        log.info(f"Server overloaded, waiting {wait_time}s for server recovery...")
                        time.sleep(wait_time)
                        continue
                    # Dopo tutti i retry, lancia errore specifico 503
                    raise ServiceError(f"Lidarr server unavailable (503) for {method} {endpoint} after {max_retries} attempts", "lidarr")
                
                response.raise_for_status()
                return response.json() if response.content else None
                
            except requests.exceptions.Timeout:
                elapsed = time.time() - start_time
                self.operation_stats["timeouts"] += 1
                log.warning(f"Lidarr timeout: {method} {endpoint} after {elapsed:.2f}s (attempt {attempt+1}/{max_retries})")
                if attempt < max_retries - 1:
                    # Per timeout su lookup, aumenta delay per dare tempo al server
                    delay_multiplier = 3 if 'lookup' in endpoint else 1
                    wait_time = retry_delay * (attempt + 1) * delay_multiplier
                    log.info(f"Waiting {wait_time}s before retry due to timeout...")
                    time.sleep(wait_time)
                    continue
                raise ServiceError(f"Lidarr timeout for {method} {endpoint} after {elapsed:.2f}s (tried {max_retries} times)", "lidarr")
                
            except RateLimitError:
                # Re-raise rate limit errors
                raise
                
            except Exception as e:
                elapsed = time.time() - start_time
                self.operation_stats["errors"] += 1
                log.warning(f"Lidarr error: {method} {endpoint} after {elapsed:.2f}s - {e} (attempt {attempt+1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                raise ServiceError(f"Lidarr error for {method} {endpoint} after {elapsed:.2f}s: {e}", "lidarr", e)
        
        return None
    
    def test_connection(self) -> bool:
        """Test connettività e autenticazione Lidarr"""
        try:
            status = self._lidarr_request("GET", "system/status")
            return status and "version" in status
        except Exception as e:
            log.error(f"Lidarr connection test failed: {e}")
            return False
    
    def add_artist(self, artist_info: ArtistInfo) -> bool:
        """Aggiunge artista alla libreria Lidarr"""
        # Quick health check se abbiamo molti 503 errors recenti
        if self.operation_stats["server_unavailable_503"] >= 3:
            log.warning(f"Skipping artist {artist_info.name} - Lidarr server has {self.operation_stats['server_unavailable_503']} recent 503 errors")
            return False
            
        # Check se artista già esiste
        existing = self.get_artist(artist_info.mbid)
        if existing:
            log.debug(f"Artist {artist_info.name} already exists")
            return True
        
        # Lookup artista in Lidarr DB
        try:
            search_results = self._lidarr_request(
                "GET", "artist/lookup", 
                params={"term": f"mbid:{artist_info.mbid}"}
            )
            
            if not search_results:
                log.warning(f"Artist {artist_info.name} not found in Lidarr database")
                return False
            
            artist_data = search_results[0]
            
            # Payload per aggiunta artista
            payload = {
                "foreignArtistId": artist_info.mbid,
                "artistName": artist_info.name,
                "monitored": artist_info.monitored,
                "rootFolderPath": self.config["LIDARR_ROOT_FOLDER"],
                "qualityProfileId": self.config.get("LIDARR_QUALITY_PROFILE_ID", 1),
                "metadataProfileId": self.config.get("LIDARR_METADATA_PROFILE_ID", 1),
                "addOptions": {
                    "monitor": self.config.get("LIDARR_MONITOR_MODE", "all"),
                    "searchForMissingAlbums": self.config.get("LIDARR_SEARCH_ON_ADD", True)
                }
            }
            
            # Merge con dati Lidarr
            payload.update({
                k: v for k, v in artist_data.items() 
                if k in ["artistType", "disambiguation", "overview", "images", "links", "genres"]
            })
            
            result = self._lidarr_request("POST", "artist", json=payload)
            if result:
                log.info(f"Added artist {artist_info.name} to Lidarr")
                return True
            return False
            
        except Exception as e:
            log.error(f"Failed to add artist {artist_info.name}: {e}")
            return False
    
    def get_artist(self, mbid: str) -> Optional[ArtistInfo]:
        """Recupera info artista se esiste in Lidarr"""
        try:
            artists = self._lidarr_request("GET", "artist")
            if not artists:
                return None
                
            for artist in artists:
                if artist.get("foreignArtistId") == mbid:
                    return ArtistInfo(
                        mbid=mbid,
                        name=artist["artistName"],
                        service_id=str(artist["id"]),
                        monitored=artist["monitored"]
                    )
            return None
        except Exception as e:
            log.error(f"Failed to get artist {mbid}: {e}")
            return None
    
    def refresh_artist(self, mbid: str) -> bool:
        """Aggiorna metadati artista in Lidarr"""
        artist = self.get_artist(mbid)
        if not artist or not artist.service_id:
            log.warning(f"Artist {mbid} not found for refresh")
            return False
        
        try:
            payload = {
                "name": "RefreshArtist",
                "artistId": int(artist.service_id)
            }
            result = self._lidarr_request("POST", "command", json=payload)
            return result is not None
        except Exception as e:
            log.error(f"Failed to refresh artist {mbid}: {e}")
            return False
    
    def add_album(self, album_info: AlbumInfo) -> bool:
        """Aggiunge album alla libreria Lidarr"""
        try:
            # Cerca album esistente
            artist = self.get_artist(album_info.artist_mbid)
            if not artist:
                log.error(f"Artist not found for album {album_info.title}")
                return False
            
            # Check if album already exists
            albums = self._lidarr_request("GET", "album", params={"artistId": artist.service_id})
            if albums:
                for album in albums:
                    if album.get("foreignAlbumId") == album_info.mbid:
                        log.debug(f"Album {album_info.title} already exists")
                        return True
            
            # Lookup album in Lidarr DB
            search_results = self._lidarr_request(
                "GET", "album/lookup",
                params={"term": f"mbid:{album_info.mbid}"}
            )
            
            if not search_results:
                log.warning(f"Album {album_info.title} not found in Lidarr database")
                return False
            
            album_data = search_results[0]
            
            # Payload album
            payload = {
                "foreignAlbumId": album_info.mbid,
                "artistId": int(artist.service_id),
                "monitored": True,
                "addOptions": {
                    "searchForNewAlbum": self.config.get("LIDARR_SEARCH_ON_ADD", True)
                }
            }
            
            # Merge con dati Lidarr
            payload.update({
                k: v for k, v in album_data.items()
                if k in ["title", "releaseDate", "images", "links", "genres", "disambiguation"]
            })
            
            result = self._lidarr_request("POST", "album", json=payload)
            if result:
                log.info(f"Added album {album_info.title} to Lidarr")
                return True
            return False
            
        except Exception as e:
            log.error(f"Failed to add album {album_info.title}: {e}")
            return False
    
    def queue_album(self, album_info: AlbumInfo, force_new: bool = False) -> bool:
        """Accoda album per download in Lidarr"""
        try:
            # Find album in Lidarr
            artist = self.get_artist(album_info.artist_mbid)
            if not artist:
                log.error(f"Artist not found for album {album_info.title}")
                return False
            
            albums = self._lidarr_request("GET", "album", params={"artistId": artist.service_id})
            target_album = None
            if albums:
                for album in albums:
                    if album.get("foreignAlbumId") == album_info.mbid:
                        target_album = album
                        break
            
            if not target_album:
                log.warning(f"Album {album_info.title} not found in library")
                return False
            
            # Trigger search
            command_payload = {
                "name": "AlbumSearch",
                "albumIds": [target_album["id"]]
            }
            
            result = self._lidarr_request("POST", "command", json=command_payload)
            if result:
                log.info(f"Queued album {album_info.title} for search")
                return True
            return False
            
        except Exception as e:
            log.error(f"Failed to queue album {album_info.title}: {e}")
            return False
    
    def force_search(self) -> bool:
        """Forza ricerca generale in Lidarr"""
        try:
            # Equivalent to HP forceSearch - rescan for missing
            payload = {
                "name": "ApplicationUpdateRescan"
            }
            result = self._lidarr_request("POST", "command", json=payload)
            if result:
                log.info("Triggered force search/rescan in Lidarr")
                return True
            return False
        except Exception as e:
            log.error(f"Failed to force search: {e}")
            return False
    
    def get_service_info(self) -> Dict[str, Any]:
        """Info servizio per diagnostica con performance stats"""
        try:
            status = self._lidarr_request("GET", "system/status")
            
            # Calcola average response time
            avg_time = (self.operation_stats["total_time"] / self.operation_stats["total_requests"] 
                       if self.operation_stats["total_requests"] > 0 else 0)
            
            return {
                "service": "lidarr",
                "version": status.get("version", "unknown") if status else "unknown",
                "endpoint": self.config["LIDARR_ENDPOINT"],
                "root_folder": self.config["LIDARR_ROOT_FOLDER"],
                "quality_profile": self.config.get("LIDARR_QUALITY_PROFILE_ID", 1),
                "metadata_profile": self.config.get("LIDARR_METADATA_PROFILE_ID", 1),
                "performance": {
                    "total_requests": self.operation_stats["total_requests"],
                    "avg_response_time": f"{avg_time:.2f}s",
                    "timeouts": self.operation_stats["timeouts"],
                    "errors": self.operation_stats["errors"],
                    "slow_operations": self.operation_stats["slow_operations"],
                    "server_unavailable_503": self.operation_stats["server_unavailable_503"],
                    "health_status": "degraded" if self.operation_stats["server_unavailable_503"] >= 3 else "healthy"
                }
            }
        except Exception:
            return {
                "service": "lidarr", 
                "endpoint": self.config["LIDARR_ENDPOINT"],
                "status": "error",
                "performance": self.operation_stats
            }
    
    def album_exists(self, mbid: str, added_albums: set) -> bool:
        """
        Verifica se un album esiste già in Lidarr
        Compatibile con la logica HP originale
        """
        if mbid in added_albums:
            return True
            
        try:
            # Cerca in tutti gli album di Lidarr
            artists = self._lidarr_request("GET", "artist")
            if not artists:
                return False
                
            for artist in artists:
                albums = self._lidarr_request("GET", "album", params={"artistId": artist["id"]})
                if albums:
                    for album in albums:
                        if album.get("foreignAlbumId") == mbid:
                            if self.config.get("DEBUG_PRINT", False):
                                print(f"[DEBUG] Album {mbid} trovato in Lidarr")
                            return True
            
            if self.config.get("DEBUG_PRINT", False):
                print(f"[DEBUG] Album {mbid} non trovato in Lidarr")
            return False
            
        except Exception as e:
            log.error(f"Lidarr album_exists failed for {mbid}: {e}")
            return False
    
    @classmethod
    def get_config_requirements(cls) -> Dict[str, Any]:
        """Requisiti di configurazione per Lidarr"""
        return {
            "required": ["LIDARR_API_KEY", "LIDARR_ENDPOINT", "LIDARR_ROOT_FOLDER"],
            "optional": {
                "LIDARR_QUALITY_PROFILE_ID": {"default": 1, "type": "int"},
                "LIDARR_METADATA_PROFILE_ID": {"default": 1, "type": "int"},
                "LIDARR_MONITOR_MODE": {"default": "all", "type": "str"},
                "LIDARR_SEARCH_ON_ADD": {"default": True, "type": "bool"},
                "LIDARR_MAX_RETRIES": {"default": 3, "type": "int"},
                "LIDARR_RETRY_DELAY": {"default": 5, "type": "int"},
                "LIDARR_TIMEOUT": {"default": 60, "type": "int"},
                "DEBUG_PRINT": {"default": False, "type": "bool"}
            }
        }