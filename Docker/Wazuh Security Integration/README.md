# Security Integration Guide

This repository contains guides and configuration files for integrating Wazuh, OpenCTI, and Microsoft 365 Defender.

## Directory Structure

```
security-integration/
├── README.md
├── docker/
│   ├── docker-compose.yml
│   └── .env.example
├── guides/
│   ├── wazuh-opencti-integration.md
│   └── microsoft-defender-opencti-integration.md
└── scripts/
    └── wazuh-opencti-script.sh
```

## Quick Start

1. Clone this repository
2. Copy the `.env.example` file to `.env` and update with your credentials
3. Deploy the stack using `docker-compose up -d`
4. Follow the integration guides in the `guides/` directory

## Components

- **Wazuh**: Open source security monitoring
- **OpenCTI**: Open source threat intelligence platform
- **Microsoft 365 Defender**: Microsoft's cloud-based security solution

## Integration Overview

This project enables:
- Wazuh alerts to be sent to OpenCTI for threat intelligence correlation
- Microsoft 365 Defender alerts and incidents to be imported into OpenCTI
- Centralized visibility of security events across your infrastructure