#!/bin/bash

function check_if_root {
  if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit
  fi
}

function create_directories {
  mkdir -p gitlab/config | true
  mkdir -p gitlab/logs | true
  mkdir -p gitlab/data | true

  mkdir -p gitlab/config/ssl | true
  chmod 755 gitlab/config/ssl
}

CRON_SCRIPT=$(pwd)/cron.sh

function add_crontab {
    echo -e "0\t1\t20\t*\t*\troot\t/bin/bash -c \"$CRON_SCRIPT $DOMAIN\"" >> /etc/crontab
}

function remove_crontab {
    sed -i "\/bin\/bash/d" /etc/crontab
}

function restart_cron {
    systemctl restart crond
    systemctl restart synoscheduler
}

function run_docker_compose {
    docker-compose up -d
}

function stop_docker_compose {
    docker-compose down
}

# argument parsing for start or stop
if [ "$1" == "start" ]; then
    # read second argument as domain
    DOMAIN=$2
    if [ -z "$DOMAIN" ]; then
        echo "Usage: $0 start <domain>"
        exit 1
    fi
    check_if_root
    create_directories
    /bin/bash -c "$CRON_SCRIPT $DOMAIN"
    run_docker_compose
    add_crontab
elif [ "$1" == "stop" ]; then
    check_if_root
    stop_docker_compose
    remove_crontab
else
    echo "Usage: $0 start|stop"
    exit 1
fi
