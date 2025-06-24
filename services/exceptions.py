"""
DiscoveryLastFM v2.0 - Custom Exceptions
Service-specific exceptions for error handling
"""


class ServiceError(Exception):
    """Eccezione generica per errori dei servizi musicali"""
    
    def __init__(self, message: str, service: str = "unknown", original_error: Exception = None):
        self.service = service
        self.original_error = original_error
        super().__init__(f"[{service}] {message}")


class ConfigurationError(Exception):
    """Eccezione per errori di configurazione"""
    
    def __init__(self, message: str, missing_keys: list = None):
        self.missing_keys = missing_keys or []
        super().__init__(message)


class ConnectionError(ServiceError):
    """Eccezione per errori di connessione ai servizi"""
    pass


class AuthenticationError(ServiceError):
    """Eccezione per errori di autenticazione"""
    pass


class RateLimitError(ServiceError):
    """Eccezione per errori di rate limiting"""
    
    def __init__(self, message: str, service: str = "unknown", retry_after: int = None):
        self.retry_after = retry_after
        super().__init__(message, service)


class NotFoundError(ServiceError):
    """Eccezione per risorse non trovate"""
    pass