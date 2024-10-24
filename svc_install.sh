#!/bin/bash
echo Before installing service, configure WorkingDirectory and ExecStart in otroserver.service
echo Hit any key to continue...
read -n 1 -s
sudo cp otroserver.service /etc/systemd/system/otroserver.service
sudo systemctl daemon-reload
sudo systemctl enable otroserver