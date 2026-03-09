#!/bin/bash

echo "========================================="
echo "Instalando ODBC Driver for SQL Server"
echo "========================================="

echo "1. Agregando clave GPG de Microsoft..."
curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | sudo gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg

echo "2. Agregando repositorio Microsoft..."
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/ubuntu/20.04/prod focal main" | sudo tee /etc/apt/sources.list.d/mssql-release.list

echo "3. Actualizando paquetes..."
sudo apt-get update

echo "4. Instalando ODBC Driver 18 y herramientas..."
ACCEPT_EULA=Y sudo apt-get install -y msodbcsql18 mssql-tools18

echo "5. Agregando msodbcsql al archivo odbcinst.ini..."
sudo odbcinst -i -d -n "ODBC Driver 18 for SQL Server"

echo "========================================="
echo "Instalación completada!"
echo "========================================="
