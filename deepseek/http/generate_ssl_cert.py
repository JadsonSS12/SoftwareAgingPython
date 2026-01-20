"""
Generate self-signed SSL certificate for development
"""

import subprocess
import os
import sys

def generate_ssl_certificate(hostname="localhost", days=365):
    """Generate self-signed SSL certificate"""
    print("🔐 Generating self-signed SSL certificate...")
    
    # Create key
    subprocess.run([
        "openssl", "genrsa",
        "-out", "key.pem",
        "2048"
    ], check=True)
    
    # Create certificate signing request
    subprocess.run([
        "openssl", "req", "-new",
        "-key", "key.pem",
        "-out", "csr.pem",
        "-subj", f"/CN={hostname}"
    ], check=True)
    
    # Create certificate
    subprocess.run([
        "openssl", "x509", "-req",
        "-in", "csr.pem",
        "-signkey", "key.pem",
        "-out", "cert.pem",
        "-days", str(days)
    ], check=True)
    
    # Clean up CSR
    if os.path.exists("csr.pem"):
        os.remove("csr.pem")
    
    print("✅ SSL certificate generated:")
    print(f"   Certificate: cert.pem")
    print(f"   Private Key: key.pem")
    print(f"   Valid for: {days} days")
    print(f"   Hostname: {hostname}")
    
    # Set permissions
    os.chmod("key.pem", 0o600)
    os.chmod("cert.pem", 0o644)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        hostname = sys.argv[1]
    else:
        hostname = "localhost"
    
    if len(sys.argv) > 2:
        days = int(sys.argv[2])
    else:
        days = 365
    
    try:
        generate_ssl_certificate(hostname, days)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error generating certificate: {e}")
        print("\n📋 Make sure OpenSSL is installed:")
        print("   Ubuntu/Debian: sudo apt-get install openssl")
        print("   macOS: brew install openssl")
        print("   Windows: Download from https://slproweb.com/products/Win32OpenSSL.html")
    except FileNotFoundError:
        print("❌ OpenSSL not found. Please install OpenSSL first.")