#!/bin/bash
# Script para conectarse a RDS y ejecutar el script de inicialización

echo "🔌 Conectando a RDS para inicializar bases de datos..."

# Obtener endpoints
MAIN_DB=$(terraform output -raw main_db_endpoint)
PERSISTENCE_DB=$(terraform output -raw persistence_db_endpoint)

echo "Main DB Endpoint: $MAIN_DB"
echo "Persistence DB Endpoint: $PERSISTENCE_DB"

# Extraer solo el hostname (sin puerto)
MAIN_DB_HOST=$(echo $MAIN_DB | cut -d: -f1)
PERSISTENCE_DB_HOST=$(echo $PERSISTENCE_DB | cut -d: -f1)

echo ""
echo "Hostname Main DB: $MAIN_DB_HOST"
echo "Hostname Persistence DB: $PERSISTENCE_DB_HOST"

# Solicitar contraseña
echo ""
echo "📝 Ingresa la contraseña de la base de datos (de terraform.tfvars):"
read -s DB_PASSWORD

echo ""
echo "🚀 Ejecutando script de inicialización..."
echo "   (Esto creará las tablas y datos de ejemplo)"

# Ejecutar script SQL
mysql -h "$MAIN_DB_HOST" -P 3306 -u admin -p"$DB_PASSWORD" < scripts/init_database.sql

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Bases de datos inicializadas correctamente!"
    echo ""
    echo "Verifica que las tablas se crearon:"
    echo "  mysql -h $MAIN_DB_HOST -P 3306 -u admin -p -e \"USE order_management; SHOW TABLES;\""
    echo "  mysql -h $PERSISTENCE_DB_HOST -P 3306 -u admin -p -e \"USE persistence; SELECT * FROM bodega_items;\""
else
    echo ""
    echo "❌ Error al inicializar bases de datos"
    echo "   Verifica:"
    echo "   - Que estás en la misma VPC o usando un bastion host"
    echo "   - Que el security group permite conexiones en puerto 3306"
    echo "   - Que la contraseña es correcta"
fi

