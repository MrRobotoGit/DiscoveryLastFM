"""
DiscoveryLastFM v2.1 - Services Module
Music service abstractions for Headphones and Lidarr integration
"""

__version__ = "2.1.0"
__author__ = "MrRobotoGit"

from .factory import MusicServiceFactory
from .base import ArtistInfo, AlbumInfo, MusicServiceBase
from .exceptions import ServiceError, ConfigurationError

__all__ = [
    'MusicServiceFactory',
    'ArtistInfo', 
    'AlbumInfo',
    'MusicServiceBase',
    'ServiceError',
    'ConfigurationError'
]