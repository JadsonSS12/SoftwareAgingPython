"""
Environment configuration and validation
"""

import os
from typing import Optional

class ServerConfig:
    """Server configuration with validation"""
    
    @staticmethod
    def get_host() -> str:
        return os.getenv("HOST", "0.0.0.0")
    
    @staticmethod
    def get_port() -> int:
        return int(os.getenv("PORT", "8081"))
    
    @staticmethod
    def is_ssl_enabled() -> bool:
        return os.getenv("SSL_ENABLED", "false").lower() == "true"
    
    @staticmethod
    def get_ssl_cert_path() -> Optional[str]:
        certfile = os.getenv("SSL_CERTFILE", "cert.pem")
        return certfile if os.path.exists(certfile) else None
    
    @staticmethod
    def get_ssl_key_path() -> Optional[str]:
        keyfile = os.getenv("SSL_KEYFILE", "key.pem")
        return keyfile if os.path.exists(keyfile) else None
    
    @staticmethod
    def validate_config():
        """Validate server configuration"""
        errors = []
        
        # Validate SSL configuration
        if ServerConfig.is_ssl_enabled():
            cert_path = ServerConfig.get_ssl_cert_path()
            key_path = ServerConfig.get_ssl_key_path()
            
            if not cert_path:
                errors.append("SSL certificate file not found")
            if not key_path:
                errors.append("SSL key file not found")
        
        # Validate port
        port = ServerConfig.get_port()
        if not (1 <= port <= 65535):
            errors.append(f"Port {port} is invalid. Must be between 1 and 65535")
        
        if errors:
            raise ValueError("Configuration errors:\n- " + "\n- ".join(errors))
        
        return True