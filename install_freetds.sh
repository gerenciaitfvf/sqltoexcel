#!/bin/bash

echo "========================================="
echo "Instalando FreeTDS para SQL Server"
echo "========================================="

sudo apt-get update
sudo apt-get install -y unixodbc unixodbc-dev freetds-dev freetds-bin

echo "Configurando FreeTDS..."
echo "[global]
tds version = 7.4
dump file = /tmp/freetds.log
timeout = 10
connect timeout = 10" | sudo tee /etc/freetds/freetds.conf

echo "========================================="
echo "Instalación completada!"
echo "========================================="
