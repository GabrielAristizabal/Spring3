#!/bin/bash

# IP pública o privada del verificador de consistencia
VERIFICADOR_IP=44.223.35.185

# Puerto donde corre el verificador
VERIFICADOR_PORT=8080

# Endpoint de health check
HEALTH_ENDPOINT="/health"

# Intervalo entre checks (en segundos)
INTERVAL=5

# Directorio de logs (si no existe, se crea automáticamente)
LOG_DIR="/home/ubuntu/logs"
LOG_FILE="$LOG_DIR/monitor_verificador.log"


# PREPARAR DIRECTORIO DE LOGS

# Crear directorio si no existe
mkdir -p "$LOG_DIR"

# Crear archivo de log si no existe
if [ ! -f "$LOG_FILE" ]; then
    touch "$LOG_FILE"
fi


# INICIO DEL MONITOR

echo "=== Monitor del Verificador de Consistencia ==="
echo "Verificando cada $INTERVAL segundos..."
echo "Destino: http://$VERIFICADOR_IP:$VERIFICADOR_PORT$HEALTH_ENDPOINT"
echo "Logs: $LOG_FILE"
echo "==============================================="

while true; do

    # Obtener código HTTP del endpoint
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$VERIFICADOR_IP:$VERIFICADOR_PORT$HEALTH_ENDPOINT)

    # Registrar estado
    if [ "$STATUS" -ne 200 ]; then
        echo "[ERROR] Verificador NO responde (HTTP $STATUS) - $(date)" >> "$LOG_FILE"
    else
        echo "[OK] Verificador activo - $(date)" >> "$LOG_FILE"
    fi

    sleep $INTERVAL
done
