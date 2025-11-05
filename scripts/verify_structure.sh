#!/bin/bash
# Script para verificar la estructura del proyecto antes de ejecutar terraform init

echo "🔍 Verificando estructura del proyecto..."
echo ""

# Verificar directorio actual
echo "📁 Directorio actual: $(pwd)"
echo ""

# Verificar archivos principales
echo "📄 Verificando archivos principales..."
[ -f "main.tf" ] && echo "✅ main.tf" || echo "❌ main.tf faltante"
[ -f "variables.tf" ] && echo "✅ variables.tf" || echo "❌ variables.tf faltante"
[ -f "outputs.tf" ] && echo "✅ outputs.tf" || echo "❌ outputs.tf faltante"
echo ""

# Verificar módulos
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

ALL_MODULES_OK=true
for module in "${MODULES[@]}"; do
    if [ -d "$module" ]; then
        if [ -f "$module/main.tf" ]; then
            echo "✅ $module"
        else
            echo "⚠️  $module (sin main.tf)"
            ALL_MODULES_OK=false
        fi
    else
        echo "❌ $module (no existe)"
        ALL_MODULES_OK=false
    fi
done

echo ""
if [ "$ALL_MODULES_OK" = true ]; then
    echo "✅ Todos los módulos están presentes"
else
    echo "❌ Faltan algunos módulos"
    echo ""
    echo "💡 Soluciones:"
    echo "   1. Verifica que clonaste todo el repositorio: git pull"
    echo "   2. Verifica que los módulos están en el repositorio remoto"
    echo "   3. Si los módulos no están en Git, agrégalos:"
    echo "      git add modules/"
    echo "      git commit -m 'Add modules'"
    echo "      git push"
    exit 1
fi

# Verificar funciones Lambda
echo ""
echo "🔧 Verificando funciones Lambda..."
LAMBDA_FUNCTIONS=(
    "modules/lambda/functions/create_order.py"
    "modules/lambda/functions/validator.py"
    "modules/lambda/functions/anomaly.py"
    "modules/lambda/functions/sync.py"
    "modules/lambda/functions/audit.py"
    "modules/lambda/functions/check_consistency.py"
)

for func in "${LAMBDA_FUNCTIONS[@]}"; do
    if [ -f "$func" ]; then
        echo "✅ $func"
    else
        echo "⚠️  $func (faltante, se puede crear después)"
    fi
done

# Verificar configuración de Terraform
echo ""
echo "⚙️  Verificando configuración de Terraform..."
if [ ! -d "$HOME/.terraform.d/plugin-cache" ]; then
    echo "⚠️  Plugin cache directory no existe"
    echo "   Ejecuta: mkdir -p ~/.terraform.d/plugin-cache"
else
    echo "✅ Plugin cache directory existe"
fi

if [ -f "terraform.tfvars" ]; then
    echo "✅ terraform.tfvars existe"
else
    echo "⚠️  terraform.tfvars no existe"
    if [ -f "terraform.tfvars.example" ]; then
        echo "   Puedes crear uno desde: cp terraform.tfvars.example terraform.tfvars"
    fi
fi

echo ""
echo "✅ Verificación completada!"
echo ""
echo "Si todos los módulos están presentes, puedes ejecutar:"
echo "  terraform init"

