"""
DiscoveryLastFM v2.0 - Lidarr Service  
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
        """Richiesta unificata con retry logic identica a HP"""
        url = f"{self.config['LIDARR_ENDPOINT'].rstrip('/')}/api/v1/{endpoint.lstrip('/')}"
        headers = {
            "X-Api-Key": self.config["LIDARR_API_KEY"],
            "Content-Type": "application/json"
        }
        
        # Configurazione retry consistente con HP
        max_retries = self.config.get("LIDARR_MAX_RETRIES", 3)
        retry_delay = self.config.get("LIDARR_RETRY_DELAY", 5)
        timeout = self.config.get("LIDARR_TIMEOUT", 60)
        
        for attempt in range(max_retries):
            try:
                if self.config.get("DEBUG_PRINT", False):
                    print(f"[DEBUG] Lidarr {method} → {url}")
                
                response = requests.request(
                    method, url, headers=headers, timeout=timeout, **kwargs
                )
                
                if self.config.get("DEBUG_PRINT", False):
                    print(f"[DEBUG] Lidarr ← {response.status_code}")
                
                # Gestione rate limiting Lidarr
                if response.status_code == 429:
                    wait_time = int(response.headers.get("Retry-After", retry_delay * 2))
                    if attempt < max_retries - 1:
                        log.warning(f"Lidarr rate limit, waiting {wait_time}s")
                        time.sleep(wait_time)
                        continue
                    raise RateLimitError(f"Rate limit exceeded", "lidarr", wait_time)
                
                response.raise_for_status()
                return response.json() if response.content else None
                
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                raise ServiceError(f"Lidarr timeout for {method} {endpoint}", "lidarr")
                
            except RateLimitError:
                # Re-raise rate limit errors
                raise
                
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                raise ServiceError(f"Lidarr error for {method} {endpoint}: {e}", "lidarr", e)
        
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
        """Info servizio per diagnostica"""
        try:
            status = self._lidarr_request("GET", "system/status")
            return {
                "service": "lidarr",
                "version": status.get("version", "unknown") if status else "unknown",
                "endpoint": self.config["LIDARR_ENDPOINT"],
                "root_folder": self.config["LIDARR_ROOT_FOLDER"],
                "quality_profile": self.config.get("LIDARR_QUALITY_PROFILE_ID", 1),
                "metadata_profile": self.config.get("LIDARR_METADATA_PROFILE_ID", 1)
            }
        except Exception:
            return {
                "service": "lidarr", 
                "endpoint": self.config["LIDARR_ENDPOINT"],
                "status": "error"
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