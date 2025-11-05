"""
Emisor de Auditoría
Este componente genera un reporte de inconsistencia cuando se detecta que un pedido no puede ser satisfecho.
"""
import json
import os
import pymysql
import boto3
import logging
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sns_client = boto3.client('sns')

def get_db_connection():
    """Establece conexión con la base de datos"""
    try:
        db_endpoint = os.environ.get('DB_ENDPOINT', '')
        db_host = db_endpoint.split(':')[0] if ':' in db_endpoint else db_endpoint
        connection = pymysql.connect(
            host=db_host,
            user=os.environ.get('DB_USERNAME', 'admin'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'order_management'),
            connect_timeout=10,
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as e:
        logger.error(f"Error conectando a la base de datos: {str(e)}")
        raise

def generar_reporte_inconsistencia(pedido_id: int, items_faltantes: list, connection):
    """Genera y guarda un reporte de inconsistencia en la base de datos"""
    try:
        with connection.cursor() as cursor:
            # Insertar reporte
            sql = """
                INSERT INTO reportes_inconsistencia 
                (pedido_id, items_faltantes, fecha_deteccion, estado)
                VALUES (%s, %s, %s, 'pendiente')
            """
            items_json = json.dumps(items_faltantes)
            now = datetime.now()
            cursor.execute(sql, (pedido_id, items_json, now))
            connection.commit()
            
            reporte_id = cursor.lastrowid
            logger.info(f"Reporte de inconsistencia {reporte_id} creado para pedido {pedido_id}")
            return reporte_id
    except Exception as e:
        logger.error(f"Error generando reporte para pedido {pedido_id}: {str(e)}")
        raise

def actualizar_estado_pedido_fallido(pedido_id: int, connection):
    """Marca el pedido como fallido"""
    try:
        with connection.cursor() as cursor:
            sql = """
                UPDATE pedidos
                SET estado = 'fallido_por_disponibilidad',
                    fecha_fallo = %s,
                    ultima_actualizacion = %s
                WHERE pedido_id = %s
            """
            now = datetime.now()
            cursor.execute(sql, (now, now, pedido_id))
            connection.commit()
            logger.info(f"Pedido {pedido_id} marcado como fallido")
    except Exception as e:
        logger.error(f"Error actualizando estado del pedido {pedido_id}: {str(e)}")
        raise

def lambda_handler(event, context):
    """
    Handler principal de Lambda
    Genera reportes de auditoría para pedidos inconsistentes.
    """
    logger.info(f"Evento recibido: {json.dumps(event)}")
    
    connection = None
    reportes_generados = []
    
    try:
        # Procesar cada registro de SNS
        for record in event.get('Records', []):
            try:
                # Parsear mensaje SNS
                message_body = json.loads(record['Sns']['Message'])
                
                pedido_id = message_body.get('pedido_id')
                es_consistente = message_body.get('es_consistente', True)
                items_faltantes = message_body.get('items_faltantes', [])
                
                if not pedido_id:
                    logger.error("Mensaje sin pedido_id")
                    continue
                
                if es_consistente:
                    logger.warning(f"Pedido {pedido_id} es consistente, no debería estar aquí")
                    continue
                
                logger.warning(f"Generando reporte de inconsistencia para pedido {pedido_id}")
                
                # Conectar a base de datos
                connection = get_db_connection()
                
                # Generar reporte
                reporte_id = generar_reporte_inconsistencia(pedido_id, items_faltantes, connection)
                
                # Actualizar estado del pedido
                actualizar_estado_pedido_fallido(pedido_id, connection)
                
                # Publicar en topic de auditoría
                audit_topic_arn = os.environ['AUDIT_TOPIC_ARN']
                
                reporte = {
                    'reporte_id': reporte_id,
                    'pedido_id': pedido_id,
                    'items_faltantes': items_faltantes,
                    'fecha_deteccion': datetime.now().isoformat(),
                    'tipo': 'inconsistencia_disponibilidad'
                }
                
                sns_client.publish(
                    TopicArn=audit_topic_arn,
                    Message=json.dumps(reporte),
                    Subject=f"Reporte Inconsistencia Pedido {pedido_id}",
                    MessageAttributes={
                        'pedido_id': {
                            'DataType': 'String',
                            'StringValue': str(pedido_id)
                        },
                        'tipo': {
                            'DataType': 'String',
                            'StringValue': 'inconsistencia_disponibilidad'
                        }
                    }
                )
                
                logger.info(f"Reporte de inconsistencia {reporte_id} generado y publicado para pedido {pedido_id}")
                
                reportes_generados.append(reporte)
                
                # Cerrar conexión
                if connection:
                    connection.close()
                    connection = None
                
            except Exception as e:
                logger.error(f"Error procesando mensaje: {str(e)}", exc_info=True)
                if connection:
                    connection.close()
                    connection = None
                raise
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'mensaje': 'Auditoría completada',
                'reportes_generados': reportes_generados
            })
        }
        
    except Exception as e:
        logger.error(f"Error fatal en lambda_handler: {str(e)}", exc_info=True)
        if connection:
            connection.close()
        raise

