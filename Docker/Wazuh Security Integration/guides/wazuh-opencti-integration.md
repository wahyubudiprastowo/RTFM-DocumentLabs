# Wazuh to OpenCTI Integration Guide

## Prerequisites
- Wazuh server running at https://10.90.4.49
- OpenCTI running at http://10.90.4.48:8080
- Admin access to both platforms

## Step 1: Configure OpenCTI to accept Wazuh data

1. After updating the docker-compose.yml file with the Wazuh connector, restart your OpenCTI containers:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

2. Log in to OpenCTI at http://10.90.4.48:8080 with your credentials:
   - Username: ithelp@digiserve.coid
   - Password: D1g15ervE

3. Navigate to Data > Connectors

4. Verify that the Wazuh connector is running and properly configured.

## Step 2: Configure Wazuh to send alerts to OpenCTI

1. Log in to your Wazuh dashboard at https://10.90.4.49 with credentials:
   - Username: admin
   - Password: ewr6fIh2c8ZsjSzIzxxHKa*JZSD.esmx

2. Navigate to Management > Configuration

3. Configure the Wazuh Integrator module to send alerts to OpenCTI:
   
   a. Edit the ossec.conf file (on the Wazuh manager):
   ```xml
   <ossec_config>
     <integration>
       <name>custom-opencti</name>
       <hook_url>http://10.90.4.48:8080/graphql</hook_url>
       <api_key>9f0b864d-e7ec-4575-ae08-d4c55d96fca4</api_key>
       <level>7</level>
       <rule_id>100200,100201,100202</rule_id>
       <alert_format>json</alert_format>
     </integration>
   </ossec_config>
   ```

   b. Create a custom integration script at /var/ossec/integrations/custom-opencti:
   ```bash
   #!/bin/bash
   
   WEBHOOK_URL="$1"
   API_KEY="$2"
   ALERT_FILE="$3"
   
   if [ ! -f ${ALERT_FILE} ]; then
     echo "Error: ${ALERT_FILE} does not exist"
     exit 1
   fi
   
   # Format alert for OpenCTI
   ALERT_JSON="$(cat ${ALERT_FILE})"
   
   # Send to OpenCTI
   curl -X POST "${WEBHOOK_URL}" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer ${API_KEY}" \
     -d "{\"query\":\"mutation ImportPush(\$file: Upload!) { importPush(file: \$file) }\",\"variables\":{\"file\": {\"fileName\":\"wazuh-alert.json\",\"contentType\":\"application/json\",\"body\":${ALERT_JSON}}}}"
   
   exit 0
   ```

   c. Make the script executable:
   ```bash
   chmod +x /var/ossec/integrations/custom-opencti
   ```

   d. Restart Wazuh:
   ```bash
   systemctl restart wazuh-manager
   ```

## Step 3: Test the Integration

1. Generate a test alert in Wazuh by running a command that triggers an alert, such as:
   ```bash
   /var/ossec/bin/agent_control -r -a
   ```

2. Check in OpenCTI that the alert has been received:
   - Navigate to Data > Entities > Incidents
   - You should see new incidents imported from Wazuh

## Step 4: Configure Alert Mappings (Optional but Recommended)

In OpenCTI, navigate to Settings > Customization:

1. Create appropriate mappings for how Wazuh alert fields should be translated to STIX objects:
   - Rule level → Severity
   - Rule group → Labels/Tags
   - Agent name → Source
   - etc.

2. Save your customization settings.

## Troubleshooting

If alerts are not appearing in OpenCTI:

1. Check the Wazuh integration logs:
   ```bash
   tail -f /var/ossec/logs/integrations.log
   ```

2. Check the OpenCTI connector logs:
   ```bash
   docker-compose logs connector-wazuh
   ```

3. Ensure the API key and URLs are correct