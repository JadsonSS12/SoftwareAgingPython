#!/usr/bin/env python3
"""
Main entry point for the MQTT Broker Server
"""

import asyncio
import logging
import sys
import signal
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler # Importado para corrigir o erro de log

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import BrokerConfig
from src.database import DatabaseManager
from src.mqtt_broker import MQTTBrokerManager
from src.api_server import APIServer
import uvicorn

logger = logging.getLogger(__name__)

class MQTTBrokerApplication:
    def __init__(self):
        self.config = BrokerConfig()
        self.setup_logging()
        self.db_manager = DatabaseManager(self.config)
        self.mqtt_manager = MQTTBrokerManager(self.config, self.db_manager)
        self.api_server = APIServer(self.config, self.mqtt_manager, self.db_manager)
        self.shutdown_event = asyncio.Event()
        
    def setup_logging(self):
        """Setup logging configuration"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        logging_config = self.config.logging
        
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        
        # Uso do RotatingFileHandler para suportar maxBytes e backupCount
        logging.basicConfig(
            level=getattr(logging, logging_config.level),
            format=logging_config.format,
            handlers=[
                logging.StreamHandler(),
                RotatingFileHandler(
                    logging_config.file,
                    maxBytes=logging_config.max_size,
                    backupCount=logging_config.backup_count
                )
            ]
        )
        
        logging.getLogger("hbmqtt").setLevel(logging.WARNING)
        logging.getLogger("asyncio").setLevel(logging.WARNING)
        
        logger.info("Logging configured")
    
    async def start(self):
        """Start the application"""
        logger.info("Starting MQTT Broker Application...")
        
        try:
            # Create database tables
            self.db_manager.create_tables()
            
            # Start MQTT broker
            await self.mqtt_manager.start()
            
            # Start API server com loop definido explicitamente como "asyncio"
            api_config = uvicorn.Config(
                self.api_server.app,
                host=self.config.api.host,
                port=self.config.api.port,
                log_level="info" if not self.config.api.debug else "debug",
                access_log=True,
                loop="asyncio" 
            )
            
            server = uvicorn.Server(api_config)
            
            logger.info(f"API Server starting on {self.config.api.host}:{self.config.api.port}")
            logger.info(f"Dashboard available at http://{self.config.api.host}:{self.config.api.port}/")
            
            # Gather garante que ambos rodem no mesmo loop sem criar conflitos de Future
            await asyncio.gather(
                server.serve(),
                self.keep_alive(),
                return_exceptions=True
            )
            
        except Exception as e:
            logger.error(f"Failed to start application: {e}")
            await self.shutdown()
    
    async def keep_alive(self):
        """Keep the main loop alive until shutdown"""
        await self.shutdown_event.wait()
    
    async def shutdown(self):
        """Shutdown the application gracefully"""
        if self.shutdown_event.is_set():
            return
            
        logger.info("Shutting down MQTT Broker Application...")
        self.shutdown_event.set()
        
        try:
            await self.mqtt_manager.stop()
        except Exception as e:
            logger.error(f"Error stopping MQTT broker: {e}")
        
        logger.info("Shutdown complete")

def generate_ssl_certificates():
    """Generate self-signed SSL certificates if needed"""
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
    import datetime
    
    cert_dir = Path("certs")
    cert_dir.mkdir(exist_ok=True)
    
    cert_file = cert_dir / "cert.pem"
    key_file = cert_dir / "key.pem"
    
    if not cert_file.exists() or not key_file.exists():
        logger.info("Generating self-signed SSL certificates...")
        
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "MQTT Broker"),
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([x509.DNSName("localhost")]),
            critical=False,
        ).sign(private_key, hashes.SHA256())
        
        with open(key_file, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        with open(cert_file, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        logger.info(f"SSL certificates generated in {cert_dir}")

def main():
    """Main entry point"""
    generate_ssl_certificates()
    
    # Criamos a instância da App dentro de uma função assíncrona para amarrar o loop corretamente
    async def run_app():
        app = MQTTBrokerApplication()
        await app.start()

    try:
        asyncio.run(run_app())
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()