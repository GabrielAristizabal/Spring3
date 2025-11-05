#!/bin/bash
# Script para preparar las funciones Lambda y el layer de MySQL

set -e

echo "Preparando funciones Lambda y layer de MySQL..."

# Directorio base
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LAMBDA_DIR="$PROJECT_ROOT/modules/lambda"

# Crear directorio para layer
echo "1. Creando layer de MySQL..."
LAYER_DIR="$LAMBDA_DIR/layers/python"
mkdir -p "$LAYER_DIR"

# Instalar pymysql en el layer
echo "   Instalando pymysql..."
pip install pymysql -t "$LAYER_DIR" || python3 -m pip install pymysql -t "$LAYER_DIR"

# Crear ZIP del layer
echo "   Creando ZIP del layer..."
cd "$LAYER_DIR"
zip -r ../mysql-layer.zip . -q
cd "$LAMBDA_DIR"
echo "   ✅ Layer creado: layers/mysql-layer.zip"

# Crear ZIPs de las funciones Lambda
echo "2. Creando ZIPs de funciones Lambda..."
cd "$LAMBDA_DIR/functions"

for func in create_order validator anomaly sync audit check_consistency; do
    if [ -f "${func}.py" ]; then
        echo "   Creando ${func}.zip..."
        zip "${func}.zip" "${func}.py" -q
        echo "   ✅ ${func}.zip creado"
    else
        echo "   ⚠️  ${func}.py no encontrado, saltando..."
    fi
done

cd "$PROJECT_ROOT"

echo ""
echo "✅ Preparación completada!"
echo ""
echo "Archivos creados:"
echo "  - modules/lambda/layers/mysql-layer.zip"
echo "  - modules/lambda/functions/*.zip"
echo ""
echo "Ahora puedes ejecutar 'terraform init' y 'terraform apply'"

