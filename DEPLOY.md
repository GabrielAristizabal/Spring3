# Guía de Despliegue

Esta guía explica cómo desplegar el sistema de gestión de pedidos y bodega en AWS usando Terraform.

## Prerrequisitos

- Cuenta de AWS con permisos adecuados
- AWS CLI configurado (`aws configure`)
- Acceso a una región de AWS (por defecto: us-east-1)
- Credenciales de AWS configuradas

## Instalación y Despliegue

### Opción 1: Desde un repositorio Git (Recomendado)

```bash
# Clonar el repositorio
git clone https://github.com/TU_USUARIO/TU_REPOSITORIO
cd TU_REPOSITORIO/

# Cambiar a la rama de despliegue (si aplica)
git checkout Deployments  # o main/master según tu repositorio

# Instalar Terraform
sh ./install_terraform.sh

# Cambiar al directorio del proyecto (si está en un subdirectorio)
cd spring3-order-system/  # o el nombre de tu directorio

# Actualizar código (si es necesario)
git pull

# Limpiar cache de Terraform (opcional pero recomendado)
rm -rf ~/.terraform.d
rm -rf .terraform
rm -f .terraform.lock.hcl

# Configurar el proyecto
sh ./setup.sh

# Inicializar Terraform
terraform init

# Revisar plan de despliegue
terraform plan

# Aplicar cambios (desplegar infraestructura)
terraform apply
```

### Opción 2: Despliegue Local

```bash
# Si ya tienes el proyecto localmente
cd spring3-order-system/

# Ejecutar setup
sh ./setup.sh

# Inicializar Terraform
terraform init

# Verificar plan
terraform plan

# Desplegar
terraform apply
```

## Configuración Inicial

### 1. Configurar Variables

Edita `terraform.tfvars` con tus valores:

```hcl
aws_region = "us-east-1"
project_name = "spring3-order-system"
environment = "dev"

db_password = "TU_CONTRASEÑA_SEGURA_AQUI"  # ⚠️ IMPORTANTE: Cambiar esto
db_username = "admin"
```

### 2. Preparar Funciones Lambda

Antes de ejecutar `terraform apply`, asegúrate de que las funciones Lambda están preparadas:

```bash
# Ejecutar script de preparación
sh ./scripts/prepare_lambda.sh

# O manualmente en Windows
.\scripts\prepare_lambda.ps1
```

Esto creará:
- `modules/lambda/layers/mysql-layer.zip`
- `modules/lambda/functions/*.zip`

## Post-Despliegue

### 1. Inicializar Bases de Datos

Una vez desplegado, necesitas inicializar las bases de datos:

```bash
# Obtener el endpoint de la base de datos
terraform output main_db_endpoint

# Conectar a la base de datos (desde una instancia EC2 en la misma VPC o usando bastion)
mysql -h <DB_ENDPOINT> -u admin -p < scripts/init_database.sql
```

**Nota**: Necesitarás estar en la misma VPC o usar un bastion host para conectarte a RDS.

### 2. Obtener URLs del API Gateway

```bash
# Obtener la URL del API Gateway
terraform output api_gateway_url
```

### 3. Ejecutar Experimentos

```bash
# Ejecutar script de experimentos
python scripts/experimento.py https://TU_API_GATEWAY_URL
```

## Verificación

### Verificar que todo está funcionando:

1. **CloudWatch Dashboard**: Verifica logs y métricas
2. **API Gateway**: Prueba crear un pedido
3. **Lambda Functions**: Revisa logs en CloudWatch
4. **RDS**: Verifica que las bases de datos están accesibles

## Troubleshooting

### Error: "No se pueden crear las funciones Lambda"

- Verifica que los archivos ZIP existen en `modules/lambda/functions/`
- Verifica que el layer existe: `modules/lambda/layers/mysql-layer.zip`
- Ejecuta: `sh ./scripts/prepare_lambda.sh`

### Error: "No se puede conectar a RDS"

- Verifica que las funciones Lambda están en la misma VPC que RDS
- Verifica los security groups permiten conexión en puerto 3306
- Verifica que el endpoint de RDS es correcto

### Error: "Terraform no encuentra módulos"

- Ejecuta: `terraform init`
- Verifica que todos los módulos existen en `modules/`

### Error: "Credenciales de AWS no encontradas"

```bash
# Configurar AWS CLI
aws configure

# O usar variables de entorno
export AWS_ACCESS_KEY_ID="tu_access_key"
export AWS_SECRET_ACCESS_KEY="tu_secret_key"
export AWS_DEFAULT_REGION="us-east-1"
```

## Comandos Útiles

```bash
# Ver outputs después del despliegue
terraform output

# Ver estado actual
terraform show

# Destruir toda la infraestructura (¡CUIDADO!)
terraform destroy

# Formatear código Terraform
terraform fmt

# Validar configuración
terraform validate
```

## Estructura Esperada en el Repositorio

```
TU_REPOSITORIO/
├── spring3-order-system/          # o el nombre que prefieras
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── terraform.tfvars.example
│   ├── install_terraform.sh
│   ├── setup.sh
│   ├── modules/
│   │   ├── networking/
│   │   ├── databases/
│   │   ├── messaging/
│   │   ├── lambda/
│   │   ├── django/
│   │   ├── monitoring/
│   │   └── api_gateway/
│   └── scripts/
│       ├── init_database.sql
│       ├── experimento.py
│       ├── prepare_lambda.sh
│       └── prepare_lambda.ps1
└── README.md
```

## Notas Importantes

1. **Costos**: El despliegue crea recursos que generan costos en AWS. Usa `terraform destroy` para eliminar todo cuando no lo necesites.

2. **Contraseñas**: Nunca commitees `terraform.tfvars` con contraseñas reales. Está en `.gitignore`.

3. **Tiempo de Despliegue**: El despliegue completo puede tardar 15-20 minutos debido a las instancias RDS.

4. **Región**: Asegúrate de que todos los recursos se crean en la misma región.

5. **Permisos IAM**: Necesitas permisos para crear:
   - VPC, Subnets, Security Groups
   - RDS instances
   - Lambda functions
   - SNS/SQS
   - ECS/Fargate
   - API Gateway
   - CloudWatch

## Soporte

Para problemas o preguntas:
- Revisa los logs de CloudWatch
- Verifica la documentación en `README.md`
- Ejecuta `terraform plan` para ver qué recursos se crearán

