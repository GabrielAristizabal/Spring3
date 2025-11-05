# Cómo Ejecutar el Experimento

## Paso 1: Obtener Información de las Bases de Datos

```bash
# Obtener endpoints de las bases de datos
terraform output main_db_endpoint
terraform output persistence_db_endpoint

# Guardar en variables para facilitar
export MAIN_DB=$(terraform output -raw main_db_endpoint)
export PERSISTENCE_DB=$(terraform output -raw persistence_db_endpoint)
echo "Main DB: $MAIN_DB"
echo "Persistence DB: $PERSISTENCE_DB"
```

## Paso 2: Inicializar las Bases de Datos

**IMPORTANTE**: Necesitas ejecutar el script SQL para crear las tablas.

### Opción A: Desde CloudShell (si tienes acceso a la VPC)

```bash
# Obtener la contraseña (la que configuraste en terraform.tfvars)
# Luego ejecutar:
MAIN_DB=$(terraform output -raw main_db_endpoint)
mysql -h $MAIN_DB -u admin -p < scripts/init_database.sql
```

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
# Configurar variables
export MAIN_DB_ENDPOINT=$(terraform output -raw main_db_endpoint)
export PERSISTENCE_DB_ENDPOINT=$(terraform output -raw persistence_db_endpoint)
export DB_USERNAME="admin"
export DB_PASSWORD="TU_CONTRASEÑA_AQUI"  # La que configuraste en terraform.tfvars

# Ejecutar experimento
python3 scripts/experimento_simplificado.py
```

### Opción B: Pasando Argumentos Directamente

```bash
MAIN_DB=$(terraform output -raw main_db_endpoint)
PERSISTENCE_DB=$(terraform output -raw persistence_db_endpoint)
DB_PASS="TU_CONTRASEÑA_AQUI"  # La de terraform.tfvars

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
MAIN_DB=$(terraform output -raw main_db_endpoint)
mysql -h $MAIN_DB -u admin -p -e "USE order_management; SHOW TABLES;"
```

### Verificar datos de ejemplo en bodega

```bash
PERSISTENCE_DB=$(terraform output -raw persistence_db_endpoint)
mysql -h $PERSISTENCE_DB -u admin -p -e "USE persistence; SELECT * FROM bodega_items;"
```

### Crear un pedido manualmente (prueba rápida)

```bash
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

### Error: "Can't connect to MySQL server"
- Verifica que estás en la misma VPC o usando un bastion host
- Verifica que el security group permite conexiones en puerto 3306
- Verifica que el endpoint es correcto

### Error: "Access denied for user"
- Verifica que la contraseña es correcta (la de terraform.tfvars)
- Verifica que el usuario es "admin"

### Error: "Table doesn't exist"
- Ejecuta el script `scripts/init_database.sql` primero

### Error: "ModuleNotFoundError: No module named 'pymysql'"
```bash
pip3 install pymysql --user
```

