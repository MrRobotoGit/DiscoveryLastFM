"""
DiscoveryLastFM v2.0 - Service Factory
Factory pattern per creazione servizi con validazione completa
"""

import logging
from typing import Dict, List, Any

from .base import MusicServiceBase
from .exceptions import ConfigurationError, ServiceError

log = logging.getLogger(__name__)


class MusicServiceFactory:
    """Factory per creazione servizi con validazione completa"""
    
    _services = {}  # Will be populated when services are imported
    
    @classmethod
    def register_service(cls, name: str, service_class):
        """Registra un servizio nel factory"""
        cls._services[name.lower()] = service_class
        log.debug(f"Registered service: {name}")
    
    @classmethod
    def create_service(cls, service_type: str, config: Dict[str, Any]) -> MusicServiceBase:
        """Crea un servizio con validazione completa"""
        service_type = service_type.lower()
        
        # Verifica che i servizi siano stati registrati
        if not cls._services:
            raise ConfigurationError("No services registered. Check service imports.")
        
        if service_type not in cls._services:
            available = ", ".join(cls._services.keys()) if cls._services else "none"
            raise ConfigurationError(f"Unknown service '{service_type}'. Available: {available}")
        
        service_class = cls._services[service_type]
        
        try:
            # Validazione configurazione prima dell'instanziazione
            log.debug(f"Validating configuration for {service_type}...")
            if not cls.validate_service_config(service_type, config):
                raise ConfigurationError(f"Invalid configuration for {service_type}")
            
            log.info(f"Creating {service_type} service...")
            service = service_class(config)
            
            # Test connessione durante la creazione con health check
            log.info(f"Testing {service_type} connection...")
            health = service.health_check()
            if health["status"] != "healthy":
                error_msg = health.get("error", "Connection failed")
                raise ServiceError(f"Cannot connect to {service_type}: {error_msg}", service_type)
            
            log.info(f"Successfully initialized {service_type} service")
            log.debug(f"Service health: {health}")
            return service
            
        except (ConfigurationError, ServiceError):
            # Re-raise service-specific errors
            raise
        except Exception as e:
            log.error(f"Failed to initialize {service_type}: {e}")
            raise ServiceError(f"Failed to initialize {service_type}: {e}", service_type, e)
    
    @classmethod
    def get_available_services(cls) -> List[str]:
        """Ritorna lista servizi disponibili"""
        return list(cls._services.keys())
    
    @classmethod 
    def validate_service_config(cls, service_type: str, config: Dict[str, Any]) -> bool:
        """Validazione config senza instanziare servizio"""
        try:
            service_class = cls._services.get(service_type.lower())
            if not service_class:
                log.warning(f"Service {service_type} not found for validation")
                return False
            
            # Validazione dry-run creando istanza temporanea
            temp_service = service_class.__new__(service_class)
            temp_service.config = config
            temp_service._validate_config()
            
            log.debug(f"Configuration valid for {service_type}")
            return True
            
        except Exception as e:
            log.warning(f"Config validation failed for {service_type}: {e}")
            return False
    
    @classmethod
    def get_service_requirements(cls, service_type: str) -> Dict[str, Any]:
        """Ritorna requisiti di configurazione per un servizio"""
        service_class = cls._services.get(service_type.lower())
        if not service_class:
            return {}
        
        # Prova a ottenere requisiti dalla classe se disponibile
        if hasattr(service_class, 'get_config_requirements'):
            return service_class.get_config_requirements()
        
        # Fallback: analizza il metodo _validate_config
        return {"note": f"Check {service_class.__name__}._validate_config() for requirements"}


# Importa e registra i servizi disponibili
def _register_available_services():
    """Registra automaticamente i servizi disponibili"""
    services_registered = []
    
    try:
        from .headphones import HeadphonesService
        MusicServiceFactory.register_service("headphones", HeadphonesService)
        services_registered.append("headphones")
    except ImportError as e:
        log.error(f"HeadphonesService not available: {e}")
    except Exception as e:
        log.error(f"Failed to register HeadphonesService: {e}")
    
    try:
        from .lidarr import LidarrService  
        MusicServiceFactory.register_service("lidarr", LidarrService)
        services_registered.append("lidarr")
    except ImportError as e:
        log.error(f"LidarrService not available: {e}")
    except Exception as e:
        log.error(f"Failed to register LidarrService: {e}")
    
    if not services_registered:
        raise ImportError("No music services could be registered")
    
    log.info(f"Successfully registered services: {', '.join(services_registered)}")
    return services_registered


# Registra servizi all'import del modulo con error handling
try:
    _register_available_services()
except Exception as e:
    log.critical(f"Service registration failed: {e}")
    # Continue but log critical error