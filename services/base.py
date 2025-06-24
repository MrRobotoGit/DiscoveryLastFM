"""
DiscoveryLastFM v2.0 - Service Base Classes
Abstract base class and data structures for music services
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class ArtistInfo:
    """Struttura dati normalizzata per artisti"""
    mbid: str
    name: str
    service_id: Optional[str] = None
    monitored: bool = True


@dataclass  
class AlbumInfo:
    """Struttura dati normalizzata per album"""
    mbid: str  # Release Group ID
    title: str
    artist_mbid: str
    artist_name: str
    release_date: Optional[str] = None
    service_id: Optional[str] = None
    queued: bool = False


class MusicServiceBase(ABC):
    """Base class per tutti i servizi musicali"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._validate_config()
    
    @abstractmethod
    def _validate_config(self) -> None:
        """Validazione configurazione specifica servizio"""
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Test connettività e autenticazione"""
        pass
    
    @abstractmethod
    def add_artist(self, artist_info: ArtistInfo) -> bool:
        """Aggiunge artista alla libreria"""
        pass
    
    @abstractmethod
    def get_artist(self, mbid: str) -> Optional[ArtistInfo]:
        """Recupera info artista se esiste"""
        pass
    
    @abstractmethod
    def refresh_artist(self, mbid: str) -> bool:
        """Aggiorna metadati artista"""
        pass
    
    @abstractmethod
    def add_album(self, album_info: AlbumInfo) -> bool:
        """Aggiunge album alla libreria"""
        pass
    
    @abstractmethod
    def queue_album(self, album_info: AlbumInfo, force_new: bool = False) -> bool:
        """Accoda album per download"""
        pass
    
    @abstractmethod
    def force_search(self) -> bool:
        """Forza ricerca generale"""
        pass
    
    @abstractmethod
    def get_service_info(self) -> Dict[str, Any]:
        """Info servizio per diagnostica"""
        pass