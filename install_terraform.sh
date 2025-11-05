#!/bin/bash
# Script para instalar Terraform en el sistema
# Compatible con sistemas Linux y macOS

set -e

echo "🔧 Instalando Terraform..."

# Detectar sistema operativo
OS="$(uname -s)"
ARCH="$(uname -m)"

case "$OS" in
    Linux*)
        echo "📦 Detectado: Linux"
        # Verificar si ya está instalado
        if command -v terraform &> /dev/null; then
            TERRAFORM_VERSION=$(terraform version -json | jq -r '.terraform_version')
            echo "✅ Terraform ya está instalado: $TERRAFORM_VERSION"
            terraform version
            exit 0
        fi
        
        # Instalar Terraform
        TERRAFORM_VERSION="1.6.0"
        TERRAFORM_URL="https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_${ARCH}.zip"
        
        echo "📥 Descargando Terraform ${TERRAFORM_VERSION}..."
        curl -o /tmp/terraform.zip "$TERRAFORM_URL"
        
        echo "📂 Extrayendo Terraform..."
        unzip -q /tmp/terraform.zip -d /tmp/
        
        echo "📋 Moviendo Terraform a /usr/local/bin..."
        sudo mv /tmp/terraform /usr/local/bin/
        
        echo "🧹 Limpiando archivos temporales..."
        rm /tmp/terraform.zip
        
        # Verificar instalación
        terraform version
        echo "✅ Terraform instalado correctamente"
        ;;
    Darwin*)
        echo "📦 Detectado: macOS"
        # Verificar si Homebrew está instalado
        if command -v brew &> /dev/null; then
            echo "📥 Instalando Terraform con Homebrew..."
            brew install terraform
            terraform version
            echo "✅ Terraform instalado correctamente"
        else
            echo "❌ Homebrew no está instalado"
            echo "   Instala Homebrew desde https://brew.sh o descarga Terraform manualmente"
            exit 1
        fi
        ;;
    *)
        echo "❌ Sistema operativo no soportado: $OS"
        echo "   Por favor, instala Terraform manualmente desde https://www.terraform.io/downloads"
        exit 1
        ;;
esac

# Verificar que Terraform funciona
if command -v terraform &> /dev/null; then
    echo ""
    echo "🎉 ¡Terraform está listo para usar!"
    terraform version
else
    echo "❌ Error: Terraform no se instaló correctamente"
    exit 1
fi

