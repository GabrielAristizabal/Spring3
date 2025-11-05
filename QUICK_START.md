# Inicio Rápido - AWS CloudShell

Esta guía es específica para ejecutar el proyecto en **AWS CloudShell**.

## Problema Común: Plugin Cache Directory

Si ves este error:
```
Error: The specified plugin cache dir /home/cloudshell-user/.terraform.d/plugin-cache cannot be opened
```

**Solución rápida:**
```bash
mkdir -p ~/.terraform.d/plugin-cache
```

## Pasos Completos en AWS CloudShell

### 1. Clonar y Preparar

```bash
# Clonar repositorio
git clone https://github.com/TU_USUARIO/TU_REPOSITORIO
cd TU_REPOSITORIO/

# Cambiar a rama correcta
git checkout Deployments  # o main/master

# Cambiar al directorio del proyecto
cd spring3-order-system/  # o el nombre de tu directorio

# Actualizar código
git pull
```

### 2. Corregir Configuración de Terraform

```bash
# Opción 1: Ejecutar script automático
chmod +x scripts/fix_terraform_cache.sh
bash scripts/fix_terraform_cache.sh

# Opción 2: Manual
mkdir -p ~/.terraform.d/plugin-cache
```

### 3. Verificar Estructura del Proyecto

```bash
# Verificar que todos los módulos están presentes
chmod +x scripts/verify_structure.sh
bash scripts/verify_structure.sh
```

**Si faltan módulos**, significa que no se subieron al repositorio. Solución:
```bash
# Desde tu máquina local, asegúrate de que los módulos están en Git
git add modules/
git commit -m "Add Terraform modules"
git push

# Luego en CloudShell
git pull
```

Este script verificará:
- ✅ Que todos los módulos existen
- ✅ Que las funciones Lambda están presentes
- ✅ Que terraform.tfvars está configurado
- ✅ Corregirá el plugin cache directory

### 4. Limpiar Cache (si es necesario)

```bash
rm -rf ~/.terraform.d
rm -rf .terraform
rm -f .terraform.lock.hcl
```

### 5. Configurar Variables

```bash
# Si no existe terraform.tfvars
cp terraform.tfvars.example terraform.tfvars

# Editar con tus valores
nano terraform.tfvars
# o
vi terraform.tfvars
```

**Valores mínimos requeridos:**
- `aws_region`: Región de AWS (ej: "us-east-1")
- `db_password`: Contraseña segura para RDS

### 6. Preparar Funciones Lambda (Opcional)

```bash
# Solo si quieres preparar los ZIPs ahora
# Nota: En CloudShell puede que no tengas pip instalado
chmod +x scripts/prepare_lambda.sh
bash scripts/prepare_lambda.sh
```

**Nota:** Si no puedes preparar los ZIPs ahora, Terraform creará las funciones sin código inicialmente. Puedes subirlas después.

### 7. Inicializar Terraform

```bash
terraform init
```

Si todavía ves errores sobre módulos:
- Verifica que estás en el directorio correcto: `pwd`
- Lista los módulos: `ls -la modules/`
- Verifica que git clonó todo: `git status`

### 8. Revisar Plan

```bash
terraform plan
```

### 9. Desplegar

```bash
terraform apply
```

## Verificación de Estructura

Ejecuta este comando para verificar que todo está en su lugar:

```bash
echo "Verificando estructura..."
[ -f "main.tf" ] && echo "✅ main.tf" || echo "❌ main.tf faltante"
[ -d "modules/networking" ] && echo "✅ modules/networking" || echo "❌ modules/networking faltante"
[ -d "modules/databases" ] && echo "✅ modules/databases" || echo "❌ modules/databases faltante"
[ -d "modules/messaging" ] && echo "✅ modules/messaging" || echo "❌ modules/messaging faltante"
[ -d "modules/lambda" ] && echo "✅ modules/lambda" || echo "❌ modules/lambda faltante"
[ -d "modules/django" ] && echo "✅ modules/django" || echo "❌ modules/django faltante"
[ -d "modules/monitoring" ] && echo "✅ modules/monitoring" || echo "❌ modules/monitoring faltante"
[ -d "modules/api_gateway" ] && echo "✅ modules/api_gateway" || echo "❌ modules/api_gateway faltante"
```

## Troubleshooting

### Error: "Unreadable module directory"

**Causa:** Los módulos no están en el repositorio o no se clonaron correctamente.

**Solución:**

1. **Verificar que los módulos existen localmente:**
```bash
ls -la modules/
```

2. **Si no existen en CloudShell, verificar que están en el repositorio:**
```bash
# En CloudShell
git status
git pull

# Verificar qué archivos están en el repositorio
git ls-tree -r HEAD --name-only | grep "^modules/"
```

3. **Si los módulos NO están en el repositorio, agregarlos desde tu máquina local:**
```bash
# En tu máquina local (donde tienes los módulos)
git add modules/
git commit -m "Add Terraform modules"
git push origin Deployments  # o main/master según tu rama

# Luego en CloudShell
git pull
```

4. **Verificar estructura después del pull:**
```bash
bash scripts/verify_structure.sh
```

### Error: "modules directory not found"

**Solución:**
```bash
# Verifica tu ubicación actual
pwd

# Deberías estar en: ~/TU_REPOSITORIO/spring3-order-system/
# Si no, cambia al directorio correcto
cd ~/TU_REPOSITORIO/spring3-order-system/
```

### Error: Plugin Cache Directory

**Solución:**
```bash
mkdir -p ~/.terraform.d/plugin-cache
```

### Los módulos no se subieron a Git

Si los módulos no están en el repositorio, necesitas subirlos:

```bash
# Verificar qué archivos están siendo rastreados
git status

# Agregar módulos al repositorio
git add modules/
git commit -m "Add Terraform modules"
git push
```

## Comandos Útiles

```bash
# Ver estructura del proyecto
tree -L 3 -I '.terraform'

# Verificar que todos los módulos tienen main.tf
find modules -name "main.tf" -type f

# Verificar archivos de Terraform
find . -name "*.tf" -type f | head -20
```

## Estructura Esperada

```
.
├── main.tf
├── variables.tf
├── outputs.tf
├── terraform.tfvars.example
├── modules/
│   ├── networking/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── databases/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── messaging/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── lambda/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── functions/
│   │       ├── create_order.py
│   │       ├── validator.py
│   │       ├── anomaly.py
│   │       ├── sync.py
│   │       ├── audit.py
│   │       └── check_consistency.py
│   ├── django/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── monitoring/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── api_gateway/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
└── scripts/
    ├── init_database.sql
    ├── experimento.py
    └── prepare_lambda.sh
```

## Siguiente Paso

Una vez que `terraform init` funcione correctamente, continúa con:
- `terraform plan` - Para ver qué se va a crear
- `terraform apply` - Para desplegar la infraestructura

