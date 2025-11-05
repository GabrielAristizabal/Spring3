#!/bin/bash
# Script rápido para crear ZIPs necesarios

echo "🔧 Creando archivos ZIP necesarios..."

# Crear directorio para layer
mkdir -p modules/lambda/layers/python

# Instalar pymysql
echo "📦 Instalando pymysql..."
pip3 install pymysql -t modules/lambda/layers/python --quiet || pip install pymysql -t modules/lambda/layers/python --quiet

# Crear ZIP del layer
echo "📦 Creando mysql-layer.zip..."
cd modules/lambda/layers/python
zip -r ../mysql-layer.zip . -q
cd ../../../../

# Crear ZIPs de funciones Lambda
echo "📦 Creando ZIPs de funciones Lambda..."
cd modules/lambda/functions

for func in create_order validator anomaly sync audit check_consistency; do
    if [ -f "${func}.py" ]; then
        zip "${func}.zip" "${func}.py" -q
        echo "   ✅ ${func}.zip"
    fi
done

cd ../../..

echo ""
echo "✅ Archivos ZIP creados!"
echo ""
echo "Verifica que existen:"
echo "  ls -la modules/lambda/layers/mysql-layer.zip"
echo "  ls -la modules/lambda/functions/*.zip"

