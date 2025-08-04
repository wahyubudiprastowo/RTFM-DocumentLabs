#!/bin/bash

# read first argument as domain
DOMAIN=$1
# check if domain is empty
if [ -z "$DOMAIN" ]; then
    echo "Usage: $0 <domain>"
    exit 1
fi

function copy_certs() {
    CERT_DIR="/usr/syno/etc/certificate/_archive"
    DEFAULT_CERT=$(cat $CERT_DIR/DEFAULT)
    
    rm -f gitlab/config/ssl/$DOMAIN.crt
    cp $CERT_DIR/$DEFAULT_CERT/fullchain.pem gitlab/config/ssl/$DOMAIN.crt
    chmod 644 gitlab/config/ssl/$DOMAIN.crt
    
    rm -f gitlab/config/ssl/$DOMAIN.key
    cp $CERT_DIR/$DEFAULT_CERT/privkey.pem gitlab/config/ssl/$DOMAIN.key
    chmod 644 gitlab/config/ssl/$DOMAIN.key
}

function reload_gitlab {
    GITLAB_CONTAINER_NAME="gitlab"
    docker exec -it $GITLAB_CONTAINER_NAME gitlab-ctl hup nginx
    docker exec -it $GITLAB_CONTAINER_NAME gitlab-ctl hup registry
}

copy_certs
reload_gitlab
