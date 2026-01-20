import os
import yaml
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pydantic import BaseModel
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class MQTTConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 1883
    websocket_port: int = 8883
    ssl_port: int = 8884
    max_connections: int = 10000
    keepalive: int = 60
    persistence: bool = True

class AuthUser(BaseModel):
    username: str
    password: str
    permissions: List[Dict[str, Any]] = field(default_factory=list)

class AuthConfig(BaseModel):
    enabled: bool = False
    users: List[AuthUser] = field(default_factory=list)

class APIConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    api_key: Optional[str] = None

class DatabaseConfig(BaseModel):
    url: str = "sqlite:///./mqtt_broker.db"
    echo: bool = False

class LoggingConfig(BaseModel):
    level: str = "INFO"
    file: str = "logs/mqtt_broker.log"
    max_size: int = 10485760
    backup_count: int = 5
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

class SSLConfig(BaseModel):
    enabled: bool = False
    certfile: Optional[str] = None
    keyfile: Optional[str] = None
    ca_certs: Optional[str] = None

class SecurityConfig(BaseModel):
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

class BrokerConfig:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.mqtt = MQTTConfig()
        self.auth = AuthConfig()
        self.api = APIConfig()
        self.database = DatabaseConfig()
        self.logging = LoggingConfig()
        self.ssl = SSLConfig()
        self.security = SecurityConfig()
        self.load_config()

    def load_config(self):
        """Load configuration from YAML file"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config_data = yaml.safe_load(f)
                    
                # Resolve environment variables
                config_data = self._resolve_env_vars(config_data)
                
                # Update configurations
                if 'mqtt' in config_data:
                    self.mqtt = MQTTConfig(**config_data['mqtt'])
                if 'auth' in config_data:
                    self.auth = AuthConfig(**config_data['auth'])
                if 'api' in config_data:
                    self.api = APIConfig(**config_data['api'])
                if 'database' in config_data:
                    self.database = DatabaseConfig(**config_data['database'])
                if 'logging' in config_data:
                    self.logging = LoggingConfig(**config_data['logging'])
                if 'ssl' in config_data:
                    self.ssl = SSLConfig(**config_data['ssl'])
                if 'security' in config_data:
                    self.security = SecurityConfig(**config_data['security'])
                    
                logger.info(f"Configuration loaded from {self.config_path}")
                
            except Exception as e:
                logger.error(f"Error loading config: {e}")
                raise
        else:
            logger.warning(f"Config file {self.config_path} not found, using defaults")

    def _resolve_env_vars(self, config_data: Any) -> Any:
        """Resolve environment variables in config data"""
        if isinstance(config_data, dict):
            return {k: self._resolve_env_vars(v) for k, v in config_data.items()}
        elif isinstance(config_data, list):
            return [self._resolve_env_vars(item) for item in config_data]
        elif isinstance(config_data, str) and config_data.startswith('${') and config_data.endswith('}'):
            env_var = config_data[2:-1]
            if ':' in env_var:
                var_name, default = env_var.split(':', 1)
                return os.getenv(var_name, default)
            else:
                return os.getenv(env_var, config_data)
        else:
            return config_data

    def get_mqtt_broker_config(self) -> Dict[str, Any]:
        """Get HBMQTT broker configuration"""
        config = {
            'listeners': {
                'default': {
                    'type': 'tcp',
                    'bind': f'{self.mqtt.host}:{self.mqtt.port}',
                    'max_connections': self.mqtt.max_connections,
                },
                'ws': {
                    'type': 'ws',
                    'bind': f'{self.mqtt.host}:{self.mqtt.websocket_port}',
                }
            },
            'sys_interval': 10,
            'auth': {
                'allow-anonymous': not self.auth.enabled,
                'plugins': ['auth.file', 'auth.anonymous'] if self.auth.enabled else ['auth.anonymous'],
            },
            'topic-check': {
                'enabled': True,
                'plugins': ['topic_taboo'],
            }
        }
        
        # Add SSL listener if enabled
        if self.ssl.enabled and self.ssl.certfile and self.ssl.keyfile:
            ssl_config = {
                'type': 'tcp',
                'bind': f'{self.mqtt.host}:{self.mqtt.ssl_port}',
                'ssl': True,
                'certfile': self.ssl.certfile,
                'keyfile': self.ssl.keyfile,
            }
            if self.ssl.ca_certs:
                ssl_config['cafile'] = self.ssl.ca_certs
            config['listeners']['ssl'] = ssl_config
        
        # Add authentication if enabled
        if self.auth.enabled:
            # Create auth file for HBMQTT
            auth_file_content = ""
            for user in self.auth.users:
                auth_file_content += f"{user.username}:{user.password}\n"
            
            auth_file_path = "mqtt_auth.txt"
            with open(auth_file_path, 'w') as f:
                f.write(auth_file_content)
            
            config['auth']['password-file'] = auth_file_path
        
        return config