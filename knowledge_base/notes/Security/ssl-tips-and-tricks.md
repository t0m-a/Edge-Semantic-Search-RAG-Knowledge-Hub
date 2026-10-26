# SSL, OpenSSL & HTTPS/HSTS Tips and Tricks

> [← Back to Main Index](README.md)

## Table of Contents

- [Generating a Strong Diffie-Hellman Parameter Key](#generating-a-strong-diffie-hellman-parameter-key)
- [OpenSSL Command-Line Inspection](#openssl-command-line-inspection)
  - [Inspecting CSRs & X.509 Certificates](#inspecting-csrs--x509-certificates)
  - [Key Fields in an X.509 Certificate](#key-fields-in-an-x509-certificate)
- [Testing TLS Connections with `openssl s_client`](#testing-tls-connections-with-openssl-s_client)
- [File Encryption & Decryption with `openssl enc`](#file-encryption--decryption-with-openssl-enc)
- [HTTPS & HSTS Configuration in Nginx](#https--hsts-configuration-in-nginx)
  - [Main Nginx TLS Configuration (`nginx.conf`)](#main-nginx-tls-configuration-nginxconf)
  - [Virtual Host HTTPS & HSTS Configuration](#virtual-host-https--hsts-configuration)
- [Useful SSL / TLS Security Links](#useful-ssl--tls-security-links)

---

## Generating a Strong Diffie-Hellman Parameter Key

Generate a 4096-bit Diffie-Hellman parameter file:

```bash
cd /etc/ssl/certs
openssl dhparam -out dhparam.pem 4096
```

Reference it in your main Nginx configuration (`nginx.conf`):

```nginx
ssl_dhparam /etc/ssl/certs/dhparam.pem;
```

---

## OpenSSL Command-Line Inspection

### Inspecting CSRs & X.509 Certificates

**Read a Certificate Signing Request (`.csr`):**

```bash
openssl req -noout -text -in file.csr
```

**Read an X.509 Certificate (`.crt` or `.pem`):**
An X.509 certificate is an encoded block of text containing a public key and identifying metadata.

```bash
openssl x509 -text -noout -in certificate.crt
```

### Key Fields in an X.509 Certificate

In addition to the public key itself, a decoded certificate contains:

| Certificate Field | Description |
| :--- | :--- |
| `Version` | X.509 certificate version |
| `Serial Number` | Unique serial number assigned by the CA |
| `Issuer` | Identity of the signing Certificate Authority (CA) |
| `Validity` (`Not Before` / `Not After`) | Validity time window |
| `Subject` | Distinguished name of the entity (country, organization, common name, email, etc.) |
| `Public-Key` | Public key algorithm and bit length |
| `Key Usage` / `Extended Key Usage` | Permitted cryptographic uses for the key |
| `Subject Key Identifier` / `Authority Key Identifier` | Fingerprints of the subject key and signing CA key |
| `Subject Alternative Name` (SAN) | Additional hostnames/domains covered by the certificate |
| `Basic Constraints` (`CA:FALSE` / `CA:TRUE`) | Indicates whether the certificate belongs to a Certificate Authority |
| `CRL Distribution Points` | URLs for Certificate Revocation Lists |

---

## Testing TLS Connections with `openssl s_client`

Connect to a remote TLS server in debug mode to inspect the certificate chain and negotiated cipher suite (do **not** include an `https://` protocol prefix):

```bash
openssl s_client -connect -debug $FQDN:PORT
openssl s_client -connect HOST:443
```

---

## File Encryption & Decryption with `openssl enc`

Encrypt and decrypt archives or files using AES-256-CBC symmetric encryption:

```bash
# Encrypt keys.tar.gz to keys.tar.gz.enc
openssl enc -e -aes-256-cbc -in keys.tar.gz -out keys.tar.gz.enc

# Decrypt infos.txt.enc to tmp
openssl enc -d -aes-256-cbc -in infos.txt.enc -out tmp
```

---

## HTTPS & HSTS Configuration in Nginx

### Main Nginx TLS Configuration (`nginx.conf`)

Declare strong cipher suites ordered from strongest to weakest (keep `ssl_ciphers` on a single line in production configs) and disable SSLv3 (POODLE mitigation):

```nginx
ssl_protocols TLSv1 TLSv1.1 TLSv1.2; # Dropping SSLv3, ref: POODLE
ssl_prefer_server_ciphers on;
ssl_ciphers 'ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-DSS-AES128-GCM-SHA256:kEDH+AESGCM:ECDHE-RSA-AES128-SHA256:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA:ECDHE-ECDSA-AES128-SHA:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES256-SHA:ECDHE-ECDSA-AES256-SHA:DHE-RSA-AES128-SHA256:DHE-RSA-AES128-SHA:DHE-DSS-AES128-SHA256:DHE-RSA-AES256-SHA256:DHE-DSS-AES256-SHA:DHE-RSA-AES256-SHA:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!3DES:!MD5:!PSK';
ssl_dhparam /etc/ssl/certs/dhparam.pem;
```

### Virtual Host HTTPS & HSTS Configuration

Configure certificate paths, SSL session caching, and the `Strict-Transport-Security` (HSTS) header:

```nginx
ssl_certificate             /path/to/fullchain.pem;
ssl_certificate_key         /path/to/privkey.pem;
ssl_session_cache           shared:SSL:10m;
ssl_session_timeout         10m;
keepalive_timeout           60;
ssl_ciphers                 HIGH:!aNULL:!MD5;
ssl_prefer_server_ciphers   on;
add_header Strict-Transport-Security "max-age=31536000; includeSubdomains";
```

---

## Useful SSL / TLS Security Links

- [testssl.sh — Testing TLS/SSL Encryption Anywhere on Any Port](https://testssl.sh/) ([GitHub Repository](https://github.com/drwetter/testssl.sh))
- [SSL Shopper — SSL Certificate Tools](https://www.sslshopper.com/)
- [Qualys SSL Labs — SSL Server Test](https://www.ssllabs.com/ssltest/index.html)
- [Weak Diffie-Hellman and the Logjam Attack (weakdh.org)](https://weakdh.org)
