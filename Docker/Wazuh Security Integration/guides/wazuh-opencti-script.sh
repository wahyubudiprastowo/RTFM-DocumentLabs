#!/bin/bash
#
# Wazuh - OpenCTI integration script
# This script sends Wazuh alerts to OpenCTI
#
# Copyright (C) 2024 Digiserve
#

WEBHOOK_URL="$1"
API_KEY="$2"
ALERT_FILE="$3"

if [ ! -f ${ALERT_FILE} ]; then
  echo "Error: ${ALERT_FILE} does not exist"
  exit 1
fi

# Format alert for OpenCTI
ALERT_JSON="$(cat ${ALERT_FILE})"

# Log the event (remove in production to avoid leaking sensitive data)
echo "$(date) - Sending alert to OpenCTI" >> /var/ossec/logs/integrations.log

# Send to OpenCTI
RESPONSE=$(curl -s -X POST "${WEBHOOK_URL}" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_KEY}" \
  -d "{\"query\":\"mutation ImportPush(\$file: Upload!) { importPush(file: \$file) }\",\"variables\":{\"file\": {\"fileName\":\"wazuh-alert.json\",\"contentType\":\"application/json\",\"body\":${ALERT_JSON}}}}")

# Check if the request was successful
if echo "$RESPONSE" | grep -q "errors"; then
  echo "$(date) - Error sending alert to OpenCTI: $RESPONSE" >> /var/ossec/logs/integrations.log
  exit 1
else
  echo "$(date) - Alert successfully sent to OpenCTI" >> /var/ossec/logs/integrations.log
  exit 0
fi