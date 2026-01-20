"""
Production Server Runner
Supports both HTTP and HTTPS with SSL/TLS certificates
"""

import uvicorn
import argparse
import sys
from pathlib import Path

def run_http_server(host: str = "0.0.0.0", port: int = 8000, workers: int = 4):
    """Run HTTP server"""
    print(f"🚀 Starting HTTP server on http://{host}:{port}")
    print(f"📊 Workers: {workers}")
    print(f"📚 API Documentation: http://{host}:{port}/docs")
    print(f"🏥 Health Check: http://{host}:{port}/health")
    
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        workers=workers,
        log_level="info",
        access_log=True,
        use_colors=True
    )

def run_https_server(
    host: str = "0.0.0.0",
    port: int = 8443,
    workers: int = 4,
    certfile: str = "cert.pem",
    keyfile: str = "key.pem"
):
    """Run HTTPS server with SSL/TLS"""
    cert_path = Path(certfile)
    key_path = Path(keyfile)
    
    if not cert_path.exists():
        print(f"❌ Certificate file not found: {certfile}")
        print("💡 Generate self-signed certificate with:")
        print("   python server.py --generate-cert")
        sys.exit(1)
    
    if not key_path.exists():
        print(f"❌ Key file not found: {keyfile}")
        sys.exit(1)
    
    print(f"🔒 Starting HTTPS server on https://{host}:{port}")
    print(f"📊 Workers: {workers}")
    print(f"🔐 Certificate: {certfile}")
    print(f"🔑 Key: {keyfile}")
    print(f"📚 API Documentation: https://{host}:{port}/docs")
    print(f"🏥 Health Check: https://{host}:{port}/health")
    
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        workers=workers,
        ssl_certfile=certfile,
        ssl_keyfile=keyfile,
        log_level="info",
        access_log=True,
        use_colors=True
    )

def generate_self_signed_cert(certfile: str = "cert.pem", keyfile: str = "key.pem"):
    """Generate self-signed SSL certificate for testing"""
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        import datetime
        
        print("🔐 Generating self-signed SSL certificate...")
        
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Generate certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "State"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "City"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Organization"),
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
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.DNSName("127.0.0.1"),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256())
        
        # Write private key
        with open(keyfile, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        # Write certificate
        with open(certfile, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        print(f"✅ Certificate generated: {certfile}")
        print(f"✅ Private key generated: {keyfile}")
        print(f"⚠️  Note: This is a self-signed certificate for testing only")
        print(f"💡 For production, use certificates from a trusted CA (Let's Encrypt, etc.)")
        
    except ImportError:
        print("❌ cryptography package not installed")
        print("📦 Install with: sudo pip3 install cryptography")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="Robust HTTP/HTTPS Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run HTTP server (default)
  python server.py
  
  # Run HTTP server on custom port
  python server.py --port 3000
  
  # Run HTTPS server
  python server.py --https
  
  # Run HTTPS server with custom certificates
  python server.py --https --cert mycert.pem --key mykey.pem
  
  # Generate self-signed certificate
  python server.py --generate-cert
  
  # Run with custom number of workers
  python server.py --workers 8
        """
    )
    
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind (default: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        help="Port to bind (default: 8000 for HTTP, 8443 for HTTPS)"
    )
    
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of worker processes (default: 4)"
    )
    
    parser.add_argument(
        "--https",
        action="store_true",
        help="Enable HTTPS with SSL/TLS"
    )
    
    parser.add_argument(
        "--cert",
        default="cert.pem",
        help="SSL certificate file (default: cert.pem)"
    )
    
    parser.add_argument(
        "--key",
        default="key.pem",
        help="SSL private key file (default: key.pem)"
    )
    
    parser.add_argument(
        "--generate-cert",
        action="store_true",
        help="Generate self-signed SSL certificate and exit"
    )
    
    args = parser.parse_args()
    
    # Generate certificate if requested
    if args.generate_cert:
        generate_self_signed_cert(args.cert, args.key)
        return
    
    # Determine port
    if args.port is None:
        args.port = 8443 if args.https else 8000
    
    # Run server
    try:
        if args.https:
            run_https_server(
                host=args.host,
                port=args.port,
                workers=args.workers,
                certfile=args.cert,
                keyfile=args.key
            )
        else:
            run_http_server(
                host=args.host,
                port=args.port,
                workers=args.workers
            )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
