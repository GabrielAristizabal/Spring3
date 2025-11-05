#!/usr/bin/env python3
"""
Script para verificar consistencia de pedidos directamente en la base de datos
Versión simplificada sin Lambda/API Gateway
"""
import sys
import json
import pymysql
from typing import Dict, List, Tuple

def get_db_connection(db_endpoint, db_name, db_username, db_password):
    """Establece conexión con la base de datos"""
    return pymysql.connect(
        host=db_endpoint.split(':')[0],
        user=db_username,
        password=db_password,
        database=db_name,
        connect_timeout=10,
        cursorclass=pymysql.cursors.DictCursor
    )

def get_persistence_db_connection(db_endpoint, db_name, db_username, db_password):
    """Establece conexión con la base de datos de persistencia"""
    return pymysql.connect(
        host=db_endpoint.split(':')[0],
        user=db_username,
        password=db_password,
        database=db_name,
        connect_timeout=10,
        cursorclass=pymysql.cursors.DictCursor
    )

def get_pedido_items(pedido_id: int, connection) -> List[Dict]:
    """Obtiene la lista de items del pedido"""
    with connection.cursor() as cursor:
        sql = """
            SELECT item_id, cantidad_solicitada, nombre_item
            FROM pedido_items
            WHERE pedido_id = %s
        """
        cursor.execute(sql, (pedido_id,))
        return cursor.fetchall()

def get_bodega_items(connection) -> Dict[int, Dict]:
    """Obtiene la lista de items disponibles en bodega"""
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

def verificar_pedido(main_db_endpoint, main_db_name, persistence_db_endpoint, persistence_db_name, 
                     db_username, db_password, pedido_id):
    """Verifica la consistencia de un pedido"""
    main_connection = None
    persistence_connection = None
    
    try:
        # Conectar a ambas bases de datos
        main_connection = get_db_connection(main_db_endpoint, main_db_name, db_username, db_password)
        persistence_connection = get_persistence_db_connection(persistence_db_endpoint, persistence_db_name, db_username, db_password)
        
        # Obtener items del pedido
        pedido_items = get_pedido_items(pedido_id, main_connection)
        
        if not pedido_items:
            return {'error': f'Pedido {pedido_id} no encontrado o sin items'}
        
        # Obtener items de bodega
        bodega_items = get_bodega_items(persistence_connection)
        
        # Verificar consistencia
        es_consistente, items_faltantes = verificar_consistencia(pedido_items, bodega_items)
        
        return {
            'pedido_id': pedido_id,
            'es_consistente': es_consistente,
            'items_faltantes': items_faltantes,
            'total_items_pedido': len(pedido_items),
            'items_con_falta': len(items_faltantes),
            'mensaje': 'Consistente' if es_consistente else 'No consistente - Items faltantes detectados'
        }
        
    except Exception as e:
        return {'error': str(e)}
    finally:
        if main_connection:
            main_connection.close()
        if persistence_connection:
            persistence_connection.close()

if __name__ == "__main__":
    if len(sys.argv) < 8:
        print("Uso: python verificar_consistencia_directo.py <main_db_endpoint> <main_db_name> <persistence_db_endpoint> <persistence_db_name> <db_username> <db_password> <pedido_id>")
        sys.exit(1)
    
    main_db_endpoint = sys.argv[1]
    main_db_name = sys.argv[2]
    persistence_db_endpoint = sys.argv[3]
    persistence_db_name = sys.argv[4]
    db_username = sys.argv[5]
    db_password = sys.argv[6]
    pedido_id = int(sys.argv[7])
    
    resultado = verificar_pedido(main_db_endpoint, main_db_name, persistence_db_endpoint, 
                                 persistence_db_name, db_username, db_password, pedido_id)
    print(json.dumps(resultado, indent=2))

