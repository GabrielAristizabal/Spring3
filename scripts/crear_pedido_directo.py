#!/usr/bin/env python3
"""
Script para crear pedidos directamente en la base de datos
Versión simplificada sin Lambda/API Gateway
"""
import sys
import json
import pymysql
from datetime import datetime

def crear_pedido(db_endpoint, db_name, db_username, db_password, items):
    """Crea un nuevo pedido en la base de datos"""
    connection = None
    try:
        # Conectar a base de datos
        connection = pymysql.connect(
            host=db_endpoint.split(':')[0],
            user=db_username,
            password=db_password,
            database=db_name,
            connect_timeout=10,
            cursorclass=pymysql.cursors.DictCursor
        )
        
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
            return {'pedido_id': pedido_id, 'items': len(items)}
            
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return None
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("Uso: python crear_pedido_directo.py <db_endpoint> <db_name> <db_username> <db_password> <items_json>")
        sys.exit(1)
    
    db_endpoint = sys.argv[1]
    db_name = sys.argv[2]
    db_username = sys.argv[3]
    db_password = sys.argv[4]
    items = json.loads(sys.argv[5])
    
    resultado = crear_pedido(db_endpoint, db_name, db_username, db_password, items)
    if resultado:
        print(json.dumps(resultado))
    else:
        sys.exit(1)

