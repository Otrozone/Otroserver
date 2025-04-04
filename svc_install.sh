#!/bin/bash

SERVICE_FILE="/etc/systemd/system/otroserver.service"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"  # Current script folder

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)." 
   exit 1
fi

if [[ -f "$SERVICE_FILE" ]]; then
    echo "Service file '$SERVICE_FILE' already exists. Skipping creation."
else
    cat <<EOF > "$SERVICE_FILE"
[Unit]
Description=Otroserver
After=network.target

[Service]
# User and group to run the service
User=pi
Group=pi

# Working directory where the script is located
WorkingDirectory=$SCRIPT_DIR

# Command to execute the script (ensure full paths are used)
ExecStart=$SCRIPT_DIR/otroserver.sh

# Restart policy
Restart=always
RestartSec=5

# Environment variables (if necessary)
Environment="FLASK_ENV=production"

[Install]
WantedBy=multi-user.target
EOF


    chmod 644 "$SERVICE_FILE"

    systemctl daemon-reload
    systemctl enable otroserver.service
    systemctl start otroserver.service

    echo "Service 'otroserver' has been created and started."
fi

echo "Hit any key to continue..."
read -n 1 -s