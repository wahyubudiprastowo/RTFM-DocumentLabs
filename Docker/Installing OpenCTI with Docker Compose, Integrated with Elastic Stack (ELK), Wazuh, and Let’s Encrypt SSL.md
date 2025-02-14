
# **Comprehensive Guide: Installing OpenCTI with Docker Compose, Integrated with Elastic Stack (ELK), Wazuh, and Let’s Encrypt SSL**

This guide provides a step-by-step tutorial for installing **OpenCTI** using **Docker Compose**, integrated with **Elastic Stack (ELK)**, **Wazuh**, and secured with **Let’s Encrypt SSL**.

---

## **1. Prerequisites**

### **System Requirements:**
- **CPU:** 4 vCPUs
- **Memory:** 16GB RAM
- **Storage:** 150–200GB

### **Installed Tools:**
- Docker and Docker Compose
- Git
- Certbot (for Let’s Encrypt SSL)

### **Existing Infrastructure:**
- **Wazuh:** `https://10.90.4.1`
- **Elasticsearch:** `http://10.90.4.2:9200` (Username: `elastic`, Password: `P4ssw0rd`)
- **Kibana:** `http://10.90.4.2:5601`

---

## **2. Install Docker and Docker Compose**

```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose uuid-runtime
```

Verify installation:
```bash
docker --version
docker-compose --version
```

---

## **3. Set Up Project Directory**

```bash
mkdir ~/opencti && cd ~/opencti
git clone https://github.com/OpenCTI-Platform/docker.git
cd docker
cp .env.sample .env
```

---

## **4. Generate Required Tokens and Passwords**

```bash
export OPENCTI_ADMIN_TOKEN=$(uuidgen)
export MINIO_ROOT_USER=$(uuidgen)
export MINIO_ROOT_PASSWORD=$(uuidgen)
export CONNECTOR_HISTORY_ID=$(uuidgen)
export CONNECTOR_EXPORT_FILE_STIX_ID=$(uuidgen)
export CONNECTOR_EXPORT_FILE_CSV_ID=$(uuidgen)
export CONNECTOR_IMPORT_FILE_STIX_ID=$(uuidgen)
export CONNECTOR_IMPORT_REPORT_ID=$(uuidgen)
```

Add these values to the `.env` file:
```env
OPENCTI_ADMIN_EMAIL=admin@opencti.io
OPENCTI_ADMIN_PASSWORD=ChangeMePlease
OPENCTI_ADMIN_TOKEN=<Your Generated UUID>
MINIO_ROOT_USER=<Your Generated UUID>
MINIO_ROOT_PASSWORD=<Your Generated UUID>
RABBITMQ_DEFAULT_USER=guest
RABBITMQ_DEFAULT_PASS=guest
ELASTIC_MEMORY_SIZE=4G
CONNECTOR_HISTORY_ID=<Your Generated UUID>
CONNECTOR_EXPORT_FILE_STIX_ID=<Your Generated UUID>
CONNECTOR_EXPORT_FILE_CSV_ID=<Your Generated UUID>
CONNECTOR_IMPORT_FILE_STIX_ID=<Your Generated UUID>
CONNECTOR_IMPORT_REPORT_ID=<Your Generated UUID>
```

---

## **5. Configure Docker Compose for OpenCTI**

Edit `docker-compose.yml` to connect to existing Elasticsearch and Wazuh:
```yaml
services:
  opencti:
    image: opencti/platform:latest
    environment:
      - ELASTICSEARCH__URL=http://10.90.4.2:9200
      - ELASTICSEARCH__USERNAME=elastic
      - ELASTICSEARCH__PASSWORD=P4ssw0rd
  connector-wazuh:
    image: ghcr.io/misje/opencti-wazuh-connector:0.3.0
    restart: always
    environment:
      - TZ=UTC
      - USE_TZ=true
      - OPENCTI_URL=http://opencti:8080
      - OPENCTI_TOKEN=${OPENCTI_ADMIN_TOKEN}
      - CONNECTOR_ID=<Your Generated UUID>
      - CONNECTOR_NAME=Wazuh
      - CONNECTOR_SCOPE=Artifact,Directory,Domain-Name,Email-Addr,Hostname,IPv4-Addr,IPv6-Addr,Mac-Addr,Network-Traffic,Process,StixFile,Url,User-Account,User-Agent,Windows-Registry-Key,Windows-Registry-Value-Type,Vulnerability,Indicator
      - CONNECTOR_AUTO=true
      - CONNECTOR_LOG_LEVEL=info
      - CONNECTOR_EXPOSE_METRICS=true
      - WAZUH_APP_URL=https://wazuh.dashboard:443
      - WAZUH_OPENSEARCH_URL=https://wazuh.indexer:9200
      - WAZUH_OPENSEARCH_USERNAME=admin
      - WAZUH_OPENSEARCH_PASSWORD=SecretPassword
      - WAZUH_OPENSEARCH_VERIFY_TLS=true
      - WAZUH_TLPS=TLP:AMBER+STRICT
    volumes:
      - /var/cache/wazuh
    links:
      - opencti:opencti
    logging:
      options:
        max-size: 50m
```

---

## **6. Install Certbot for Let’s Encrypt SSL**

```bash
sudo apt-get install -y certbot
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com
```

Add SSL configuration to `docker-compose.yml` and create `nginx.conf` with mounted certificates.

---

## **7. Start Services**

```bash
docker-compose up -d
```

Verify running services:
```bash
docker-compose ps
```

Access OpenCTI at `https://yourdomain.com`.

---

## **8. Automate SSL Renewal**

Add a cron job for Certbot renewal:
```bash
sudo crontab -e
0 0 * * 0 certbot renew --post-hook "docker-compose restart opencti"
```

---

### **Congratulations!** You have successfully installed **OpenCTI** with **Docker Compose**, integrated it with your existing **Elastic Stack** and **Wazuh**, and secured it with **Let’s Encrypt SSL**. This guide ensures every command is explained in detail, making it easy to follow and understand.
