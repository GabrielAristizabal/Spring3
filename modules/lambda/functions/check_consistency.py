"""
Verificador de Consistencia
Este componente permite verificar la consistencia de un pedido existente.
Útil para experimentos de verificación post-creación.
"""
import json
import os
import pymysql
import boto3
import logging
from typing import Dict, List, Tuple

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

def get_pedido_items(pedido_id: int, connection) -> List[Dict]:
    """Obtiene la lista de items del pedido"""
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT item_id, cantidad_solicitada, nombre_item
                FROM pedido_items
                WHERE pedido_id = %s
            """
            cursor.execute(sql, (pedido_id,))
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error obteniendo items del pedido {pedido_id}: {str(e)}")
        raise

def get_bodega_items(connection) -> Dict[int, Dict]:
    """Obtiene la lista de items disponibles en bodega"""
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT item_id, cantidad_disponible, nombre_item, cantidad_reservada
                FROM bodega_items
            """
            cursor.execute(sql)
            items = cursor.fetchall()
            
            bodega_dict = {}
            for item in items:
                cantidad_disponible_real = item['cantidad_disponible'] - item.get('cantidad_reservada', 0)
                bodega_dict[item['item_id']] = {
                    'cantidad_disponible': cantidad_disponible_real,
                    'nombre_item': item['nombre_item'],
                    'cantidad_total': item['cantidad_disponible']
                }
            return bodega_dict
    except Exception as e:
        logger.error(f"Error obteniendo items de bodega: {str(e)}")
        raise

def verificar_consistencia(pedido_items: List[Dict], bodega_items: Dict) -> Tuple[bool, List[Dict]]:
    """Verifica la consistencia de un pedido"""
    items_faltantes = []
    es_consistente = True
    
    for item_pedido in pedido_items:
        item_id = item_pedido['item_id']
        cantidad_solicitada = item_pedido['cantidad_solicitada']
        nombre_item = item_pedido.get('nombre_item', f'Item {item_id}')
        
        if item_id not in bodega_items:
            items_faltantes.append({
                'item_id': item_id,
                'nombre_item': nombre_item,
                'cantidad_solicitada': cantidad_solicitada,
                'cantidad_disponible': 0,
                'razon': 'Item no existe en bodega'
            })
            es_consistente = False
            continue
        
        item_bodega = bodega_items[item_id]
        cantidad_disponible = item_bodega['cantidad_disponible']
        
        if cantidad_disponible < cantidad_solicitada:
            items_faltantes.append({
                'item_id': item_id,
                'nombre_item': nombre_item,
                'cantidad_solicitada': cantidad_solicitada,
                'cantidad_disponible': cantidad_disponible,
                'razon': f'Cantidad insuficiente. Disponible: {cantidad_disponible}, Solicitado: {cantidad_solicitada}'
            })
            es_consistente = False
    
    return es_consistente, items_faltantes

def lambda_handler(event, context):
    """
    Handler principal de Lambda
    Verifica la consistencia de un pedido existente.
    """
    logger.info(f"Evento recibido: {json.dumps(event)}")
    
    connection = None
    
    try:
        # Parsear body del request
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event
        
        pedido_id = body.get('pedido_id')
        if not pedido_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'pedido_id es requerido'})
            }
        
        # Conectar a base de datos
        connection = get_db_connection()
        
        # Obtener items del pedido
        pedido_items = get_pedido_items(pedido_id, connection)
        
        if not pedido_items:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': f'Pedido {pedido_id} no encontrado o sin items'})
            }
        
        # Obtener items de bodega
        bodega_items = get_bodega_items(connection)
        
        # Verificar consistencia
        es_consistente, items_faltantes = verificar_consistencia(pedido_items, bodega_items)
        
        resultado = {
            'pedido_id': pedido_id,
            'es_consistente': es_consistente,
            'items_faltantes': items_faltantes,
            'total_items_pedido': len(pedido_items),
            'items_con_falta': len(items_faltantes),
            'mensaje': 'Consistente' if es_consistente else 'No consistente - Items faltantes detectados'
        }
        
        logger.info(f"Verificación pedido {pedido_id}: consistente={es_consistente}")
        
        # Cerrar conexión
        if connection:
            connection.close()
        
        return {
            'statusCode': 200,
            'body': json.dumps(resultado)
        }
        
    except Exception as e:
        logger.error(f"Error fatal en lambda_handler: {str(e)}", exc_info=True)
        if connection:
            connection.close()
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

