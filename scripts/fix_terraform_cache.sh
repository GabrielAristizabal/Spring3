#!/bin/bash
# Script para corregir el problema del plugin cache directory en Terraform

set -e

echo "🔧 Corrigiendo configuración de Terraform plugin cache..."

# Crear directorio de plugin cache
TERRAFORM_CACHE_DIR="$HOME/.terraform.d/plugin-cache"
mkdir -p "$TERRAFORM_CACHE_DIR"

echo "✅ Directorio creado: $TERRAFORM_CACHE_DIR"

# Crear archivo de configuración de Terraform si no existe
TERRAFORM_CONFIG_DIR="$HOME/.terraformrc"
TERRAFORM_CONFIG_FILE="$HOME/.terraformrc"

if [ ! -f "$TERRAFORM_CONFIG_FILE" ]; then
    echo "📝 Creando archivo de configuración de Terraform..."
    cat > "$TERRAFORM_CONFIG_FILE" << EOF
plugin_cache_dir = "$TERRAFORM_CACHE_DIR"
EOF
    echo "✅ Archivo de configuración creado: $TERRAFORM_CONFIG_FILE"
else
    echo "✅ Archivo de configuración ya existe"
fi

echo ""
echo "✅ Configuración corregida!"
echo "   Ahora puedes ejecutar: terraform init"
echo ""

