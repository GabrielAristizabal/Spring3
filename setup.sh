#!/bin/bash
# Script de configuración inicial del proyecto
# Prepara el entorno para ejecutar Terraform

set -e

echo "🚀 Configurando proyecto Spring3 Order System..."

# Verificar que estamos en el directorio correcto
if [ ! -f "main.tf" ]; then
    echo "❌ Error: No se encontró main.tf"
    echo "   Asegúrate de estar en el directorio raíz del proyecto"
    exit 1
fi

# Verificar que Terraform está instalado
if ! command -v terraform &> /dev/null; then
    echo "⚠️  Terraform no está instalado"
    echo "   Ejecuta primero: sh ./install_terraform.sh"
    exit 1
fi

echo "✅ Terraform encontrado: $(terraform version | head -n 1)"

# Verificar que terraform.tfvars existe
if [ ! -f "terraform.tfvars" ]; then
    echo "📝 Creando terraform.tfvars desde ejemplo..."
    if [ -f "terraform.tfvars.example" ]; then
        cp terraform.tfvars.example terraform.tfvars
        echo "⚠️  IMPORTANTE: Edita terraform.tfvars y configura:"
        echo "   - aws_region"
        echo "   - db_password (debe ser seguro)"
        echo "   - Otros valores según necesidad"
        echo ""
        read -p "¿Deseas editar terraform.tfvars ahora? (s/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Ss]$ ]]; then
            ${EDITOR:-nano} terraform.tfvars
        fi
    else
        echo "❌ Error: No se encontró terraform.tfvars.example"
        exit 1
    fi
fi

# Preparar funciones Lambda
echo ""
echo "📦 Preparando funciones Lambda..."
if [ -f "scripts/prepare_lambda.sh" ]; then
    chmod +x scripts/prepare_lambda.sh
    ./scripts/prepare_lambda.sh
else
    echo "⚠️  Script prepare_lambda.sh no encontrado"
    echo "   Las funciones Lambda necesitan ser preparadas manualmente"
fi

# Limpiar cache de Terraform si existe
if [ -d ".terraform" ]; then
    echo ""
    echo "🧹 Limpiando cache de Terraform..."
    rm -rf .terraform
    rm -f .terraform.lock.hcl
fi

echo ""
echo "✅ Configuración completada!"
echo ""
echo "📋 Próximos pasos:"
echo "   1. Verifica que terraform.tfvars tiene los valores correctos"
echo "   2. Ejecuta: terraform init"
echo "   3. Ejecuta: terraform plan"
echo "   4. Ejecuta: terraform apply"
echo ""

