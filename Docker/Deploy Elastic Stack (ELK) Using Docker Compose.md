# Deploy Elastic Stack (ELK) Using Docker Compose

This guide provides a detailed step-by-step tutorial for deploying the Elastic Stack (Elasticsearch, Logstash, Kibana) using Docker Compose with thorough explanations for each command and configuration.

---

## 📌 **Prerequisites**
- Docker and Docker Compose installed.
- A Linux-based system (Ubuntu recommended).

---

## 📄 **Step 1: Create Project Directory**
```sh
mkdir elk-docker && cd elk-docker
```
**Explanation:**
- `mkdir elk-docker`: Creates a new directory named `elk-docker`.
- `cd elk-docker`: Changes the current working directory to `elk-docker`.

---

## 🔧 **Step 2: Create `docker-compose.yml`**
Create a `docker-compose.yml` file. This file will define the services (Elasticsearch, Logstash, Kibana) and their configurations. Save the following content into `docker-compose.yml`.

---

## 🛠️ **Step 3: Create `elasticsearch.yml`**
Create a configuration file for Elasticsearch at `./elasticsearch/elasticsearch.yml`:
```yml
network.host: 0.0.0.0
xpack.security.enabled: true
xpack.security.authc.api_key.enabled: true
```
**Explanation:**
- `network.host: 0.0.0.0`: Binds Elasticsearch to all available network interfaces.
- `xpack.security.enabled: true`: Enables X-Pack security features for Elasticsearch.
- `xpack.security.authc.api_key.enabled: true`: Enables API key authentication.

---

## 🔄 **Step 4: Build and Start Services**
Run the following command in the project directory:
```sh
docker-compose up -d
```
**Explanation:**
- `docker-compose up`: Starts the services defined in `docker-compose.yml`.
- `-d`: Runs the services in detached mode (in the background).

---

## 🖥️ **Step 5: Access Kibana**
Open `http://localhost:5601` in your browser and log in with `elastic` and your provided password.

---

## **docker-compose.yml Content with Explanation**
```yml
version: '3.8'  # Specifies the Docker Compose file format version
services:  # Defines the services to be deployed
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.17.5  # Official Elasticsearch Docker image
    container_name: elasticsearch  # Names the container "elasticsearch"
    environment:  # Sets environment variables for the container
      - discovery.type=single-node  # Runs Elasticsearch as a single-node cluster
      - bootstrap.memory_lock=true  # Prevents memory swapping
      - "ES_JAVA_OPTS=-Xms2g -Xmx2g"  # Allocates 2GB of RAM to Elasticsearch
      - xpack.security.enabled=true  # Enables security features
      - xpack.security.authc.api_key.enabled=true  # Enables API key service
    ulimits:
      memlock:
        soft: -1
        hard: -1  # Sets unlimited memory lock
    volumes:
      - /data/elasticsearch:/usr/share/elasticsearch/data  # Mounts Elasticsearch data directory
    ports:
      - "9201:9200"  # Maps port 9201 on host to 9200 in container
    restart: unless-stopped  # Restarts the container unless manually stopped

  logstash:
    image: docker.elastic.co/logstash/logstash:7.17.5
    container_name: logstash
    environment:
      LS_JAVA_OPTS: "-Xms1g -Xmx1g"  # Allocates 1GB RAM for Logstash
    volumes:
      - ./logstash-pipeline:/usr/share/logstash/pipeline  # Mounts pipeline config directory
      - ./logstash-config:/usr/share/logstash/config  # Mounts general config directory
    ports:
      - "5044:5044"  # Exposes port 5044 for Beats input
    depends_on:
      - elasticsearch  # Ensures Elasticsearch starts before Logstash
    restart: unless-stopped

  kibana:
    image: docker.elastic.co/kibana/kibana:7.17.5
    container_name: kibana
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200  # Connects Kibana to Elasticsearch
      - ELASTICSEARCH_USERNAME=elastic  # Sets Elasticsearch username
      - ELASTICSEARCH_PASSWORD=R4h4s1APWD  # Sets Elasticsearch password
      - xpack.security.enabled=true  # Enables security features for Kibana
    ports:
      - "5601:5601"  # Maps port 5601 for Kibana UI
    depends_on:
      - elasticsearch
    restart: unless-stopped

volumes:
  elasticsearch-data:
    driver: local  # Defines a local volume for Elasticsearch data
  logstash-pipeline:
    driver: local  # Defines a local volume for Logstash pipeline
  logstash-config:
    driver: local  # Defines a local volume for Logstash config
```

---

This tutorial now includes detailed explanations of each step, command, and configuration, making it easier to understand and deploy the Elastic Stack using Docker Compose.