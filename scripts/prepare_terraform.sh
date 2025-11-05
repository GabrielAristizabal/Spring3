#!/bin/bash
# Script para preparar el entorno de Terraform antes de ejecutar terraform init
# Soluciona problemas comunes en AWS CloudShell

set -e

echo "🔧 Preparando entorno de Terraform..."

# 1. Crear directorio de plugin cache si no existe
TERRAFORM_CACHE_DIR="$HOME/.terraform.d/plugin-cache"
if [ ! -d "$TERRAFORM_CACHE_DIR" ]; then
    echo "📁 Creando directorio de plugin cache..."
    mkdir -p "$TERRAFORM_CACHE_DIR"
    echo "✅ Directorio creado: $TERRAFORM_CACHE_DIR"
else
    echo "✅ Directorio de plugin cache ya existe"
fi

# 2. Verificar que estamos en el directorio correcto
if [ ! -f "main.tf" ]; then
    echo "❌ Error: No se encontró main.tf en el directorio actual"
    echo "   Directorio actual: $(pwd)"
    echo "   Asegúrate de estar en el directorio raíz del proyecto"
    exit 1
fi

echo "✅ main.tf encontrado"

# 3. Verificar que todos los módulos existen
echo ""
echo "📦 Verificando módulos..."

MODULES=(
    "modules/networking"
    "modules/databases"
    "modules/messaging"
    "modules/lambda"
    "modules/django"
    "modules/monitoring"
    "modules/api_gateway"
)

MISSING_MODULES=()
for module in "${MODULES[@]}"; do
    if [ ! -d "$module" ]; then
        MISSING_MODULES+=("$module")
        echo "❌ Módulo faltante: $module"
    else
        # Verificar que tiene main.tf
        if [ ! -f "$module/main.tf" ]; then
            echo "⚠️  Advertencia: $module/main.tf no encontrado"
        else
            echo "✅ $module"
        fi
    fi
done

if [ ${#MISSING_MODULES[@]} -gt 0 ]; then
    echo ""
    echo "❌ Error: Faltan los siguientes módulos:"
    for module in "${MISSING_MODULES[@]}"; do
        echo "   - $module"
    done
    echo ""
    echo "💡 Soluciones:"
    echo "   1. Asegúrate de haber clonado todo el repositorio"
    echo "   2. Verifica que estás en el directorio correcto"
    echo "   3. Ejecuta: git pull para obtener todos los archivos"
    exit 1
fi

# 4. Verificar archivos importantes de Lambda
echo ""
echo "📦 Verificando funciones Lambda..."

LAMBDA_FUNCTIONS=(
    "modules/lambda/functions/create_order.py"
    "modules/lambda/functions/validator.py"
    "modules/lambda/functions/anomaly.py"
    "modules/lambda/functions/sync.py"
    "modules/lambda/functions/audit.py"
    "modules/lambda/functions/check_consistency.py"
)

MISSING_FUNCTIONS=()
for func in "${LAMBDA_FUNCTIONS[@]}"; do
    if [ ! -f "$func" ]; then
        MISSING_FUNCTIONS+=("$func")
        echo "❌ Función faltante: $func"
    else
        echo "✅ $func"
    fi
done

if [ ${#MISSING_FUNCTIONS[@]} -gt 0 ]; then
    echo ""
    echo "⚠️  Advertencia: Faltan algunas funciones Lambda"
    echo "   Estas se pueden crear después con: sh ./scripts/prepare_lambda.sh"
fi

# 5. Limpiar cache de Terraform si existe
if [ -d ".terraform" ]; then
    echo ""
    echo "🧹 Limpiando cache de Terraform..."
    rm -rf .terraform
    echo "✅ Cache limpiado"
fi

if [ -f ".terraform.lock.hcl" ]; then
    echo "🧹 Eliminando lock file..."
    rm -f .terraform.lock.hcl
    echo "✅ Lock file eliminado"
fi

# 6. Verificar terraform.tfvars
echo ""
if [ ! -f "terraform.tfvars" ]; then
    if [ -f "terraform.tfvars.example" ]; then
        echo "📝 Creando terraform.tfvars desde ejemplo..."
        cp terraform.tfvars.example terraform.tfvars
        echo "⚠️  IMPORTANTE: Edita terraform.tfvars y configura db_password"
    else
        echo "⚠️  Advertencia: terraform.tfvars no encontrado"
    fi
else
    echo "✅ terraform.tfvars encontrado"
fi

echo ""
echo "✅ Preparación completada!"
echo ""
echo "📋 Próximos pasos:"
echo "   1. Edita terraform.tfvars si es necesario"
echo "   2. Ejecuta: terraform init"
echo "   3. Ejecuta: terraform plan"
echo "   4. Ejecuta: terraform apply"
echo ""

