# Sistema de Gestión de Pedidos y Bodega - Detección de Fallos

Este proyecto implementa un sistema completo en AWS para la gestión de pedidos y bodega, con enfoque en la **detección del 100% de las veces** cuando no hay disponibilidad de items en un pedido.

## Arquitectura

El sistema está compuesto por los siguientes componentes principales:

1. **Validador de Disponibilidad**: Lambda function que compara items del pedido con disponibilidad en bodega
2. **Gestor de Anomalías**: Lambda function que decide el flujo según el resultado de la validación
3. **Sincronizador de Estado**: Lambda function que actualiza el estado de pedidos consistentes
4. **Emisor de Auditoría**: Lambda function que genera reportes de inconsistencia
5. **Bases de Datos RDS**: MySQL para almacenar pedidos, items y bodega
6. **SNS/SQS**: Para comunicación asíncrona y garantía de procesamiento
7. **CloudWatch**: Para monitoreo y logging
8. **API Gateway**: Para exponer endpoints REST

## Características de Detección de Fallos

El sistema garantiza la detección del 100% de los fallos mediante:

- **Dead Letter Queues (DLQ)**: Mensajes que fallan son enviados a DLQ para no perderse
- **Event Source Mapping**: SQS garantiza procesamiento de todos los mensajes
- **Validación exhaustiva**: Compara cada item del pedido con disponibilidad real
- **Logging detallado**: Todos los eventos se registran en CloudWatch
- **Alarmas de monitoreo**: Alertas cuando hay errores o mensajes en DLQ

## Requisitos Previos

- AWS CLI configurado
- Terraform >= 1.0
- Python 3.11+ (para scripts de experimento)
- Acceso a AWS con permisos suficientes

## Instalación Rápida

### Desde Repositorio Git (AWS CloudShell)

```bash
# 1. Clonar repositorio
git clone https://github.com/TU_USUARIO/TU_REPOSITORIO
cd TU_REPOSITORIO/

# 2. Cambiar a rama de despliegue
git checkout Deployments  # o main/master según tu repositorio

# 3. Instalar Terraform (si es necesario)
sh ./install_terraform.sh

# 4. Cambiar al directorio del proyecto
cd spring3-order-system/  # o el nombre de tu directorio

# 5. Corregir plugin cache directory (IMPORTANTE para AWS CloudShell)
mkdir -p ~/.terraform.d/plugin-cache

# 6. Verificar estructura del proyecto
chmod +x scripts/verify_structure.sh
bash scripts/verify_structure.sh

# 7. Actualizar código
git pull

# 8. Limpiar cache de Terraform
rm -rf ~/.terraform.d
rm -rf .terraform
rm -f .terraform.lock.hcl

# 9. Configurar variables
cp terraform.tfvars.example terraform.tfvars
# Editar terraform.tfvars con tus valores

# 10. Inicializar Terraform
terraform init

# 11. Revisar plan
terraform plan

# 12. Desplegar
terraform apply
```

**⚠️ IMPORTANTE:** Si ves errores sobre módulos faltantes, verifica que todos los módulos están en el repositorio Git. Ver `QUICK_START.md` para troubleshooting detallado.

## Instalación Detallada

### 1. Configurar Variables

Copia `terraform.tfvars.example` a `terraform.tfvars` y completa los valores:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edita `terraform.tfvars` y configura:
- `aws_region`: Región de AWS
- `db_password`: Contraseña segura para las bases de datos
- Otros valores según necesidad

### 2. Preparar Funciones Lambda

Las funciones Lambda necesitan un layer con `pymysql`. Puedes crear uno manualmente o usar el script:

```bash
cd modules/lambda
mkdir -p layers
pip install pymysql -t layers/python/
cd layers && zip -r mysql-layer.zip . && cd ../..
```

Para cada función Lambda, crea el ZIP:

```bash
cd modules/lambda/functions
for func in create_order validator anomaly sync audit check_consistency; do
  zip ${func}.zip ${func}.py
done
```

### 3. Desplegar Infraestructura

```bash
terraform init
terraform plan
terraform apply
```

El despliegue puede tardar 15-20 minutos debido a las instancias RDS.

### 4. Inicializar Bases de Datos

Una vez desplegado, conecta a las bases de datos RDS y ejecuta:

```bash
mysql -h <DB_ENDPOINT> -u admin -p < scripts/init_database.sql
```

Nota: Necesitarás estar en la misma VPC o usar un bastion host.

## Uso

### Crear un Pedido

```bash
curl -X POST https://YOUR_API_GATEWAY_URL/pedidos \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"item_id": 1, "cantidad": 10, "nombre_item": "Item A"},
      {"item_id": 2, "cantidad": 5, "nombre_item": "Item B"}
    ]
  }'
```

### Verificar Consistencia

```bash
curl -X POST https://YOUR_API_GATEWAY_URL/pedidos/123/verificar-consistencia \
  -H "Content-Type: application/json" \
  -d '{
    "pedido_id": 123
  }'
```

### Ejecutar Experimentos

El script `scripts/experimento.py` ejecuta una serie de experimentos para verificar que el sistema detecta fallos correctamente:

```bash
python scripts/experimento.py https://YOUR_API_GATEWAY_URL
```

## Flujo de Procesamiento

1. **Creación de Pedido**: Se crea un pedido y se envía a la cola de validación
2. **Validación**: El validador compara items del pedido con disponibilidad en bodega
3. **Gestión de Anomalías**: 
   - Si es consistente → Sincronizador de Estado
   - Si no es consistente → Emisor de Auditoría
4. **Sincronización**: Pedidos consistentes se marcan como validados
5. **Auditoría**: Pedidos inconsistentes generan reportes de fallo

## Monitoreo

### CloudWatch Dashboard

Accede al dashboard de CloudWatch para ver:
- Invocaciones de Lambda functions
- Errores en funciones
- Logs de inconsistencias detectadas

### Alarmas

El sistema crea alarmas para:
- Errores en el validador
- Mensajes en Dead Letter Queue (indica fallos no procesados)

## Estructura del Proyecto

```
.
├── main.tf                    # Configuración principal
├── variables.tf               # Variables globales
├── outputs.tf                 # Outputs del módulo principal
├── terraform.tfvars.example   # Ejemplo de configuración
├── modules/
│   ├── networking/            # VPC, subnets, security groups
│   ├── databases/             # RDS instances
│   ├── messaging/              # SNS topics y SQS queues
│   ├── lambda/                # Lambda functions
│   │   └── functions/         # Código Python de las funciones
│   ├── django/                # ECS Fargate para Django
│   ├── monitoring/            # CloudWatch logs y dashboards
│   └── api_gateway/           # API Gateway
└── scripts/
    ├── init_database.sql      # Script de inicialización de BD
    └── experimento.py         # Script de experimentos
```

## Troubleshooting

### Las funciones Lambda no se despliegan

- Verifica que los archivos ZIP existen en `modules/lambda/functions/`
- Verifica que el layer de MySQL existe

### No se detectan fallos

- Verifica que las bases de datos están inicializadas con `scripts/init_database.sql`
- Revisa los logs de CloudWatch para el validador
- Verifica que los mensajes SQS están siendo procesados

### Error de conexión a base de datos

- Verifica que las funciones Lambda están en la misma VPC que RDS
- Verifica los security groups permiten conexión desde Lambda a RDS (puerto 3306)

## Notas Importantes

- El sistema usa **SQS Event Source Mapping** para garantizar que todos los mensajes se procesen
- **Dead Letter Queues** capturan mensajes que fallan múltiples veces
- Todas las validaciones se registran en **CloudWatch** para auditoría
- El validador compara **cantidad_disponible - cantidad_reservada** para obtener disponibilidad real

## Costos Estimados

- RDS: ~$15-20/mes (db.t3.micro)
- Lambda: Bajo (pay per use)
- SQS/SNS: Bajo (primeros 1M requests gratis)
- CloudWatch: Bajo (primeros 5GB logs gratis)
- ECS Fargate: ~$20-30/mes (2 tareas)

Total estimado: ~$40-60/mes para entorno de desarrollo

## Licencia

Este proyecto es para fines educativos y de demostración.

