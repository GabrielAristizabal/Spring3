"""
Validador de Disponibilidad
Este componente es CRÍTICO para detectar el 100% de las veces cuando no hay disponibilidad.
Realiza una comparación entre las dos listas (pedido y bodega) para identificar si las cantidades
en el pedido se pueden satisfacer con las cantidades en la bodega.
"""
import json
import os
import pymysql
import boto3
from typing import Dict, List, Tuple, Any
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sns_client = boto3.client('sns')
sqs_client = boto3.client('sqs')

def get_db_connection():
    """Establece conexión con la base de datos principal (pedidos)"""
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
        logger.error(f"Error conectando a la base de datos principal: {str(e)}")
        raise

def get_persistence_db_connection():
    """Establece conexión con la base de datos de persistencia (bodega)"""
    try:
        connection = pymysql.connect(
            host=os.environ['PERSISTENCE_DB_ENDPOINT'].split(':')[0],
            user=os.environ['DB_USERNAME'],
            password=os.environ['DB_PASSWORD'],
            database=os.environ['PERSISTENCE_DB_NAME'],
            connect_timeout=10,
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as e:
        logger.error(f"Error conectando a la base de datos de persistencia: {str(e)}")
        raise

def get_pedido_items(pedido_id: int, connection) -> List[Dict[str, Any]]:
    """Obtiene la lista de items del pedido desde la base de datos principal"""
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT item_id, cantidad_solicitada, nombre_item
                FROM pedido_items
                WHERE pedido_id = %s
            """
            cursor.execute(sql, (pedido_id,))
            items = cursor.fetchall()
            logger.info(f"Pedido {pedido_id}: {len(items)} items encontrados")
            return items
    except Exception as e:
        logger.error(f"Error obteniendo items del pedido {pedido_id}: {str(e)}")
        raise

def get_bodega_items(connection) -> Dict[int, Dict[str, Any]]:
    """Obtiene la lista de items disponibles en bodega desde persistencia"""
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT item_id, cantidad_disponible, nombre_item, cantidad_reservada
                FROM bodega_items
            """
            cursor.execute(sql)
            items = cursor.fetchall()
            
            # Convertir a diccionario por item_id para acceso rápido
            bodega_dict = {}
            for item in items:
                cantidad_disponible_real = item['cantidad_disponible'] - item.get('cantidad_reservada', 0)
                bodega_dict[item['item_id']] = {
                    'cantidad_disponible': cantidad_disponible_real,
                    'nombre_item': item['nombre_item'],
                    'cantidad_total': item['cantidad_disponible']
                }
            
            logger.info(f"Bodega: {len(bodega_dict)} items disponibles")
            return bodega_dict
    except Exception as e:
        logger.error(f"Error obteniendo items de bodega: {str(e)}")
        raise

def validar_disponibilidad(pedido_items: List[Dict], bodega_items: Dict) -> Tuple[bool, List[Dict]]:
    """
    Valida la disponibilidad de items del pedido.
    Retorna: (es_consistente, lista_items_faltantes)
    """
    items_faltantes = []
    es_consistente = True
    
    for item_pedido in pedido_items:
        item_id = item_pedido['item_id']
        cantidad_solicitada = item_pedido['cantidad_solicitada']
        nombre_item = item_pedido.get('nombre_item', f'Item {item_id}')
        
        # Verificar si el item existe en bodega
        if item_id not in bodega_items:
            logger.warning(f"Item {item_id} ({nombre_item}) NO existe en bodega")
            items_faltantes.append({
                'item_id': item_id,
                'nombre_item': nombre_item,
                'cantidad_solicitada': cantidad_solicitada,
                'cantidad_disponible': 0,
                'razon': 'Item no existe en bodega'
            })
            es_consistente = False
            continue
        
        # Verificar cantidad disponible
        item_bodega = bodega_items[item_id]
        cantidad_disponible = item_bodega['cantidad_disponible']
        
        if cantidad_disponible < cantidad_solicitada:
            logger.warning(
                f"Item {item_id} ({nombre_item}): "
                f"solicitado={cantidad_solicitada}, disponible={cantidad_disponible}"
            )
            items_faltantes.append({
                'item_id': item_id,
                'nombre_item': nombre_item,
                'cantidad_solicitada': cantidad_solicitada,
                'cantidad_disponible': cantidad_disponible,
                'razon': f'Cantidad insuficiente. Disponible: {cantidad_disponible}, Solicitado: {cantidad_solicitada}'
            })
            es_consistente = False
        else:
            logger.info(
                f"Item {item_id} ({nombre_item}): OK - "
                f"solicitado={cantidad_solicitada}, disponible={cantidad_disponible}"
            )
    
    return es_consistente, items_faltantes

def lambda_handler(event, context):
    """
    Handler principal de Lambda
    Este handler procesa mensajes de SQS que contienen información de pedidos a validar.
    """
    logger.info(f"Evento recibido: {json.dumps(event)}")
    
    connection = None
    resultados_procesados = []
    
    try:
        # Procesar cada mensaje del batch de SQS
        for record in event.get('Records', []):
            connection = None
            persistence_connection = None
            
            try:
                # Parsear mensaje SQS
                if 'body' in record:
                    body = json.loads(record['body'])
                else:
                    body = record
                
                pedido_id = body.get('pedido_id')
                if not pedido_id:
                    logger.error("Mensaje sin pedido_id")
                    continue
                
                logger.info(f"Iniciando validación para pedido {pedido_id}")
                
                # Conectar a base de datos principal (pedidos)
                connection = get_db_connection()
                
                # Obtener items del pedido desde base principal
                pedido_items = get_pedido_items(pedido_id, connection)
                
                if not pedido_items:
                    logger.warning(f"Pedido {pedido_id} no tiene items")
                    resultados_procesados.append({
                        'pedido_id': pedido_id,
                        'es_consistente': False,
                        'razon': 'Pedido sin items',
                        'items_faltantes': []
                    })
                    if connection:
                        connection.close()
                        connection = None
                    continue
                
                # Conectar a base de datos de persistencia (bodega)
                persistence_connection = get_persistence_db_connection()
                
                # Obtener items de bodega desde base de persistencia
                bodega_items = get_bodega_items(persistence_connection)
                
                # Validar disponibilidad
                es_consistente, items_faltantes = validar_disponibilidad(pedido_items, bodega_items)
                
                resultado = {
                    'pedido_id': pedido_id,
                    'es_consistente': es_consistente,
                    'items_faltantes': items_faltantes,
                    'total_items_pedido': len(pedido_items),
                    'items_con_falta': len(items_faltantes)
                }
                
                logger.info(f"Resultado validación pedido {pedido_id}: consistente={es_consistente}, faltantes={len(items_faltantes)}")
                
                # Publicar resultado en SNS para que el Gestor de Anomalías lo procese
                validation_topic_arn = os.environ['VALIDATION_TOPIC_ARN']
                sns_client.publish(
                    TopicArn=validation_topic_arn,
                    Message=json.dumps(resultado),
                    Subject=f"Validación Pedido {pedido_id}",
                    MessageAttributes={
                        'pedido_id': {
                            'DataType': 'String',
                            'StringValue': str(pedido_id)
                        },
                        'es_consistente': {
                            'DataType': 'String',
                            'StringValue': str(es_consistente)
                        }
                    }
                )
                
                resultados_procesados.append(resultado)
                
            except Exception as e:
                logger.error(f"Error procesando mensaje: {str(e)}", exc_info=True)
                raise  # Re-lanzar para que SQS reintente
            finally:
                # Cerrar conexiones
                if persistence_connection:
                    persistence_connection.close()
                if connection:
                    connection.close()
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'mensaje': 'Validación completada',
                'resultados': resultados_procesados
            })
        }
        
    except Exception as e:
        logger.error(f"Error fatal en lambda_handler: {str(e)}", exc_info=True)
        if connection:
            connection.close()
        raise

