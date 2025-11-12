#!/bin/bash

# === CONFIGURACIÓN ===

# IP pública o privada del verificador de consistencia
VERIFICADOR_IP=44.223.35.185

# Puerto donde corre el verificador
VERIFICADOR_PORT=8080

# Endpoint de health check (asegúrate que coincida con el verificador)
HEALTH_ENDPOINT="/health"

# Intervalo entre verificaciones (segundos)
INTERVAL=5

# Directorio y archivo de logs
LOG_DIR="/home/ubuntu/logs"
LOG_FILE="$LOG_DIR/monitor_verificador.log"


# === PREPARACIÓN DE LOGS ===

mkdir -p "$LOG_DIR"
touch "$LOG_FILE"


# === INICIO DEL MONITOR ===

echo "=== Monitor del Verificador de Consistencia ==="
echo "Verificando cada $INTERVAL segundos..."
echo "Destino: http://$VERIFICADOR_IP:$VERIFICADOR_PORT$HEALTH_ENDPOINT"
echo "Logs: $LOG_FILE"
echo "==============================================="

while true; do
    # Obtener código HTTP (si falla, devolver 0)
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://$VERIFICADOR_IP:$VERIFICADOR_PORT$HEALTH_ENDPOINT)

    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

    if [ "$STATUS" == "200" ]; then
        echo "[OK] Verificador activo - $TIMESTAMP" >> "$LOG_FILE"
    elif [ -z "$STATUS" ] || [ "$STATUS" == "000" ]; then
        echo "[ERROR] Verificador NO responde (sin conexión) - $TIMESTAMP" >> "$LOG_FILE"
    else
        echo "[ERROR] Verificador NO responde (HTTP $STATUS) - $TIMESTAMP" >> "$LOG_FILE"
    fi

    sleep $INTERVAL
done
