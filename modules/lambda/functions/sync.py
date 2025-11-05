"""
Sincronizador de Estado
Este componente maneja la finalización o actualización del estado del pedido cuando es consistente.
Envía el pedido validado al gestor de pedidos para su procesamiento final.
"""
import json
import os
import pymysql
import boto3
import logging
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_db_connection():
    """Establece conexión con la base de datos"""
    try:
        connection = pymysql.connect(
            host=os.environ['DB_ENDPOINT'].split(':')[0],
            user=os.environ['DB_USERNAME'],
            password=os.environ['DB_PASSWORD'],
            database=os.environ['DB_NAME'],
            connect_timeout=10,
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as e:
        logger.error(f"Error conectando a la base de datos: {str(e)}")
        raise

def actualizar_estado_pedido(pedido_id: int, connection):
    """Actualiza el estado del pedido a 'validado' o 'procesando'"""
    try:
        with connection.cursor() as cursor:
            sql = """
                UPDATE pedidos
                SET estado = 'validado',
                    fecha_validacion = %s,
                    ultima_actualizacion = %s
                WHERE pedido_id = %s
            """
            now = datetime.now()
            cursor.execute(sql, (now, now, pedido_id))
            connection.commit()
            logger.info(f"Estado del pedido {pedido_id} actualizado a 'validado'")
    except Exception as e:
        logger.error(f"Error actualizando estado del pedido {pedido_id}: {str(e)}")
        raise

def lambda_handler(event, context):
    """
    Handler principal de Lambda
    Procesa pedidos consistentes y actualiza su estado.
    """
    logger.info(f"Evento recibido: {json.dumps(event)}")
    
    connection = None
    
    try:
        # Procesar cada registro de SNS
        for record in event.get('Records', []):
            try:
                # Parsear mensaje SNS
                message_body = json.loads(record['Sns']['Message'])
                
                pedido_id = message_body.get('pedido_id')
                es_consistente = message_body.get('es_consistente', False)
                
                if not pedido_id:
                    logger.error("Mensaje sin pedido_id")
                    continue
                
                if not es_consistente:
                    logger.warning(f"Pedido {pedido_id} no es consistente, no debería estar aquí")
                    continue
                
                logger.info(f"Sincronizando estado para pedido {pedido_id}")
                
                # Conectar a base de datos
                connection = get_db_connection()
                
                # Actualizar estado del pedido
                actualizar_estado_pedido(pedido_id, connection)
                
                logger.info(f"Pedido {pedido_id} sincronizado exitosamente")
                
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
            'body': json.dumps({'mensaje': 'Sincronización completada'})
        }
        
    except Exception as e:
        logger.error(f"Error fatal en lambda_handler: {str(e)}", exc_info=True)
        if connection:
            connection.close()
        raise

