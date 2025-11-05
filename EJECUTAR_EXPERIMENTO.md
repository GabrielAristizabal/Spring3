# Cómo Ejecutar el Experimento

## Paso 1: Obtener Información de las Bases de Datos

```bash
# Obtener endpoints de las bases de datos
terraform output main_db_endpoint
terraform output persistence_db_endpoint

# Guardar en variables para facilitar (endpoints completos)
export MAIN_DB=$(terraform output -raw main_db_endpoint)
export PERSISTENCE_DB=$(terraform output -raw persistence_db_endpoint)
echo "Main DB: $MAIN_DB"
echo "Persistence DB: $PERSISTENCE_DB"

# Extraer solo los hostnames (sin puerto) - IMPORTANTE
export MAIN_DB_HOST=$(echo $MAIN_DB | cut -d: -f1)
export PERSISTENCE_DB_HOST=$(echo $PERSISTENCE_DB | cut -d: -f1)
echo "Main DB Hostname: $MAIN_DB_HOST"
echo "Persistence DB Hostname: $PERSISTENCE_DB_HOST"
```

## Paso 2: Inicializar las Bases de Datos

**IMPORTANTE**: Necesitas ejecutar el script SQL para crear las tablas.

### Opción A: Usar Script Automático (Recomendado)

```bash
# El script extrae automáticamente el hostname y te pedirá la contraseña
chmod +x CONECTAR_RDS.sh
bash CONECTAR_RDS.sh
```

### Opción B: Manualmente desde CloudShell

```bash
# Obtener endpoint y extraer hostname
MAIN_DB=$(terraform output -raw main_db_endpoint)
MAIN_DB_HOST=$(echo $MAIN_DB | cut -d: -f1)

# Conectar usando solo el hostname y especificar puerto con -P
# Te pedirá la contraseña (la que configuraste en terraform.tfvars)
mysql -h "$MAIN_DB_HOST" -P 3306 -u admin -p < scripts/init_database.sql
```

**⚠️ Nota Importante**: El endpoint de RDS incluye el puerto (ej: `hostname:3306`), pero MySQL necesita solo el hostname. Usa `cut -d: -f1` para extraer solo el hostname.

### Opción B: Usar MySQL Workbench o cliente MySQL

1. Conecta a la base de datos principal:
   - Host: `terraform output main_db_endpoint` (sin el puerto)
   - Port: `3306`
   - Usuario: `admin`
   - Contraseña: La de `terraform.tfvars`
   - Base de datos: `order_management`

2. Ejecuta el contenido de `scripts/init_database.sql`

### Opción C: Usar AWS Systems Manager Session Manager

Si tienes una instancia EC2 en la VPC, puedes conectarte vía Session Manager y ejecutar desde ahí.

## Paso 3: Instalar Dependencias Python

```bash
# Instalar pymysql
pip3 install pymysql --user

# Verificar instalación
python3 -c "import pymysql; print('pymysql instalado correctamente')"
```

## Paso 4: Ejecutar el Experimento

### Opción A: Usando Variables de Entorno (Recomendado)

```bash
# Configurar variables (los endpoints completos funcionan con los scripts Python)
export MAIN_DB_ENDPOINT=$(terraform output -raw main_db_endpoint)
export PERSISTENCE_DB_ENDPOINT=$(terraform output -raw persistence_db_endpoint)
export DB_USERNAME="admin"
export DB_PASSWORD="TU_CONTRASEÑA_AQUI"  # La que configuraste en terraform.tfvars

# Ejecutar experimento
python3 scripts/experimento_simplificado.py
```

### Opción B: Pasando Argumentos Directamente

```bash
# Obtener endpoints completos
MAIN_DB=$(terraform output -raw main_db_endpoint)
PERSISTENCE_DB=$(terraform output -raw persistence_db_endpoint)
DB_PASS="TU_CONTRASEÑA_AQUI"  # La de terraform.tfvars

# Ejecutar experimento (los scripts Python manejan el formato endpoint:puerto)
python3 scripts/experimento_simplificado.py \
  $MAIN_DB \
  $PERSISTENCE_DB \
  admin \
  "$DB_PASS"
```

## Paso 5: Verificar Resultados

El script ejecutará 5 experimentos:

1. ✅ Pedido con items disponibles → Debe ser consistente
2. ❌ Pedido con cantidad insuficiente → Debe detectar fallo
3. ❌ Pedido con item inexistente → Debe detectar fallo
4. ❌ Pedido con múltiples items faltantes → Debe detectar fallos
5. ✅ Pedido exacto → Debe ser consistente

Al final verás un resumen con la tasa de éxito.

## Comandos Útiles

### Verificar que las bases de datos están accesibles

```bash
# Obtener hostname (sin puerto) para MySQL CLI
MAIN_DB=$(terraform output -raw main_db_endpoint)
MAIN_DB_HOST=$(echo $MAIN_DB | cut -d: -f1)

mysql -h "$MAIN_DB_HOST" -P 3306 -u admin -p -e "USE order_management; SHOW TABLES;"
```

### Verificar datos de ejemplo en bodega

```bash
# Obtener hostname (sin puerto) para MySQL CLI
PERSISTENCE_DB=$(terraform output -raw persistence_db_endpoint)
PERSISTENCE_DB_HOST=$(echo $PERSISTENCE_DB | cut -d: -f1)

mysql -h "$PERSISTENCE_DB_HOST" -P 3306 -u admin -p -e "USE persistence; SELECT * FROM bodega_items;"
```

### Crear un pedido manualmente (prueba rápida)

```bash
# Los scripts Python aceptan el endpoint completo (con puerto)
MAIN_DB=$(terraform output -raw main_db_endpoint)
DB_PASS="TU_CONTRASEÑA"

python3 scripts/crear_pedido_directo.py \
  $MAIN_DB \
  order_management \
  admin \
  "$DB_PASS" \
  '[{"item_id": 1, "cantidad": 10, "nombre_item": "Item A"}]'
```

### Verificar consistencia de un pedido específico

```bash
# Los scripts Python aceptan el endpoint completo (con puerto)
MAIN_DB=$(terraform output -raw main_db_endpoint)
PERSISTENCE_DB=$(terraform output -raw persistence_db_endpoint)
DB_PASS="TU_CONTRASEÑA"

python3 scripts/verificar_consistencia_directo.py \
  $MAIN_DB \
  order_management \
  $PERSISTENCE_DB \
  persistence \
  admin \
  "$DB_PASS" \
  1  # ID del pedido
```

## Troubleshooting

### Error: "Unknown MySQL server host 'hostname:3306'"
- **Causa**: Estás usando el endpoint completo con puerto en MySQL CLI
- **Solución**: Extrae solo el hostname usando `cut -d: -f1`:
  ```bash
  MAIN_DB_HOST=$(terraform output -raw main_db_endpoint | cut -d: -f1)
  mysql -h "$MAIN_DB_HOST" -P 3306 -u admin -p
  ```
- **Nota**: Los scripts Python (`crear_pedido_directo.py` y `verificar_consistencia_directo.py`) SÍ aceptan el endpoint completo, ellos manejan el formato internamente.

### Error: "Can't connect to MySQL server"
- **Causa**: No estás en la misma VPC o el security group no permite conexiones
- **Soluciones**:
  - Si estás en CloudShell: Puede que no tengas acceso directo. Usa:
    - AWS Systems Manager Session Manager
    - Una instancia EC2 temporal en la VPC
    - Un bastion host
  - Verifica que el security group permite conexiones en puerto 3306
  - Verifica que el endpoint es correcto

### Error: "Access denied for user"
- Verifica que la contraseña es correcta (la de terraform.tfvars)
- Verifica que el usuario es "admin"

### Error: "Table doesn't exist"
- Ejecuta el script `scripts/init_database.sql` primero usando el método del Paso 2

### Error: "ModuleNotFoundError: No module named 'pymysql'"
```bash
pip3 install pymysql --user
```

### Error: "Unknown database 'order_management'"
- Las bases de datos se crean automáticamente con RDS, pero si no existen:
  ```sql
  CREATE DATABASE IF NOT EXISTS order_management;
  CREATE DATABASE IF NOT EXISTS persistence;
  ```

