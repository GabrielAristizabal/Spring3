"""
Creador de Pedido
Este componente crea un nuevo pedido y lo envía a la cola de validación.
"""
import json
import os
import pymysql
import boto3
import logging
from datetime import datetime
import uuid

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sqs_client = boto3.client('sqs')

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

def crear_pedido(items: list, connection):
    """Crea un nuevo pedido en la base de datos"""
    try:
        with connection.cursor() as cursor:
            # Crear pedido
            sql = """
                INSERT INTO pedidos (estado, fecha_creacion, ultima_actualizacion)
                VALUES ('pendiente_validacion', %s, %s)
            """
            now = datetime.now()
            cursor.execute(sql, (now, now))
            pedido_id = cursor.lastrowid
            
            # Insertar items del pedido
            for item in items:
                sql_items = """
                    INSERT INTO pedido_items (pedido_id, item_id, cantidad_solicitada, nombre_item)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(sql_items, (
                    pedido_id,
                    item['item_id'],
                    item['cantidad'],
                    item.get('nombre_item', f"Item {item['item_id']}")
                ))
            
            connection.commit()
            logger.info(f"Pedido {pedido_id} creado con {len(items)} items")
            return pedido_id
    except Exception as e:
        logger.error(f"Error creando pedido: {str(e)}")
        raise

def lambda_handler(event, context):
    """
    Handler principal de Lambda
    Crea un pedido y lo envía a la cola de validación.
    """
    logger.info(f"Evento recibido: {json.dumps(event)}")
    
    connection = None
    
    try:
        # Parsear body del request
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event
        
        items = body.get('items', [])
        if not items:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No se proporcionaron items para el pedido'})
            }
        
        # Conectar a base de datos
        connection = get_db_connection()
        
        # Crear pedido
        pedido_id = crear_pedido(items, connection)
        
        # Enviar a cola de validación
        validation_queue_url = os.environ.get('VALIDATION_QUEUE_URL')
        order_queue_url = os.environ.get('ORDER_QUEUE_URL')
        
        mensaje_validacion = {
            'pedido_id': pedido_id,
            'timestamp': datetime.now().isoformat()
        }
        
        queue_url = validation_queue_url or order_queue_url
        if queue_url:
            sqs_client.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps(mensaje_validacion),
                MessageAttributes={
                    'pedido_id': {
                        'DataType': 'String',
                        'StringValue': str(pedido_id)
                    }
                }
            )
            logger.info(f"Pedido {pedido_id} enviado a cola de validación")
        
        # Cerrar conexión
        if connection:
            connection.close()
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'mensaje': 'Pedido creado exitosamente',
                'pedido_id': pedido_id,
                'items': len(items)
            })
        }
        
    except Exception as e:
        logger.error(f"Error fatal en lambda_handler: {str(e)}", exc_info=True)
        if connection:
            connection.close()
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

