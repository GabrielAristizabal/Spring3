#!/usr/bin/env python3
"""
Script de experimento para crear un pedido y verificar su consistencia.
Este script permite probar el sistema de detección de fallos por falta de disponibilidad.
"""
import requests
import json
import time
import sys

# Configuración
API_BASE_URL = "https://YOUR_API_GATEWAY_URL"  # Reemplazar con la URL real del API Gateway

def crear_pedido(items):
    """Crea un nuevo pedido"""
    url = f"{API_BASE_URL}/pedidos"
    
    payload = {
        "items": items
    }
    
    print(f"\n📦 Creando pedido con {len(items)} items...")
    print(f"Items: {json.dumps(items, indent=2)}")
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        result = response.json()
        
        pedido_id = result.get('pedido_id')
        print(f"✅ Pedido creado exitosamente!")
        print(f"   Pedido ID: {pedido_id}")
        print(f"   Total items: {result.get('items', 0)}")
        
        return pedido_id
    except requests.exceptions.RequestException as e:
        print(f"❌ Error creando pedido: {e}")
        if hasattr(e.response, 'text'):
            print(f"   Respuesta: {e.response.text}")
        return None

def verificar_consistencia(pedido_id):
    """Verifica la consistencia de un pedido"""
    url = f"{API_BASE_URL}/pedidos/{pedido_id}/verificar-consistencia"
    
    payload = {
        "pedido_id": pedido_id
    }
    
    print(f"\n🔍 Verificando consistencia del pedido {pedido_id}...")
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        result = response.json()
        
        es_consistente = result.get('es_consistente', False)
        items_faltantes = result.get('items_faltantes', [])
        
        if es_consistente:
            print(f"✅ Pedido CONSISTENTE - Todos los items están disponibles")
            print(f"   Total items en pedido: {result.get('total_items_pedido', 0)}")
            print(f"   Items con falta: {result.get('items_con_falta', 0)}")
        else:
            print(f"❌ Pedido NO CONSISTENTE - Items faltantes detectados")
            print(f"   Total items en pedido: {result.get('total_items_pedido', 0)}")
            print(f"   Items con falta: {result.get('items_con_falta', 0)}")
            print(f"\n   Detalles de items faltantes:")
            for item in items_faltantes:
                print(f"      - Item {item.get('item_id')} ({item.get('nombre_item')}):")
                print(f"        Solicitado: {item.get('cantidad_solicitada')}")
                print(f"        Disponible: {item.get('cantidad_disponible')}")
                print(f"        Razón: {item.get('razon')}")
        
        return result
    except requests.exceptions.RequestException as e:
        print(f"❌ Error verificando consistencia: {e}")
        if hasattr(e.response, 'text'):
            print(f"   Respuesta: {e.response.text}")
        return None

def experimento_deteccion_fallos():
    """Ejecuta experimentos para probar la detección de fallos"""
    print("=" * 60)
    print("EXPERIMENTO: Detección de Fallos por Falta de Disponibilidad")
    print("=" * 60)
    
    # Experimentos
    experimentos = [
        {
            "nombre": "Experimento 1: Pedido con items disponibles",
            "items": [
                {"item_id": 1, "cantidad": 10, "nombre_item": "Item A"},
                {"item_id": 2, "cantidad": 5, "nombre_item": "Item B"}
            ],
            "esperado": "consistente"
        },
        {
            "nombre": "Experimento 2: Pedido con cantidad insuficiente",
            "items": [
                {"item_id": 1, "cantidad": 150, "nombre_item": "Item A"},  # Solo hay 100 disponibles
                {"item_id": 2, "cantidad": 5, "nombre_item": "Item B"}
            ],
            "esperado": "no_consistente"
        },
        {
            "nombre": "Experimento 3: Pedido con item que no existe",
            "items": [
                {"item_id": 999, "cantidad": 10, "nombre_item": "Item No Existente"},
                {"item_id": 1, "cantidad": 10, "nombre_item": "Item A"}
            ],
            "esperado": "no_consistente"
        },
        {
            "nombre": "Experimento 4: Pedido con múltiples items faltantes",
            "items": [
                {"item_id": 1, "cantidad": 150, "nombre_item": "Item A"},  # Insuficiente
                {"item_id": 2, "cantidad": 100, "nombre_item": "Item B"},  # Insuficiente (solo hay 50)
                {"item_id": 999, "cantidad": 10, "nombre_item": "Item No Existente"}  # No existe
            ],
            "esperado": "no_consistente"
        },
        {
            "nombre": "Experimento 5: Pedido exacto (cantidad igual a disponible)",
            "items": [
                {"item_id": 5, "cantidad": 30, "nombre_item": "Item E"}  # Exactamente 30 disponibles
            ],
            "esperado": "consistente"
        }
    ]
    
    resultados = []
    
    for i, experimento in enumerate(experimentos, 1):
        print(f"\n{'=' * 60}")
        print(f"{experimento['nombre']}")
        print(f"{'=' * 60}")
        
        # Crear pedido
        pedido_id = crear_pedido(experimento['items'])
        
        if not pedido_id:
            print("⚠️  No se pudo crear el pedido, saltando experimento...")
            continue
        
        # Esperar un poco para que se procese
        print("\n⏳ Esperando procesamiento...")
        time.sleep(3)
        
        # Verificar consistencia
        resultado = verificar_consistencia(pedido_id)
        
        if resultado:
            es_consistente = resultado.get('es_consistente', False)
            esperado_consistente = experimento['esperado'] == 'consistente'
            
            exito = (es_consistente == esperado_consistente)
            
            resultados.append({
                'experimento': experimento['nombre'],
                'pedido_id': pedido_id,
                'esperado': experimento['esperado'],
                'obtenido': 'consistente' if es_consistente else 'no_consistente',
                'exito': exito,
                'items_faltantes': len(resultado.get('items_faltantes', []))
            })
            
            if exito:
                print(f"\n✅ EXPERIMENTO EXITOSO: Resultado esperado obtenido")
            else:
                print(f"\n❌ EXPERIMENTO FALLIDO: Se esperaba {experimento['esperado']}, se obtuvo {'consistente' if es_consistente else 'no_consistente'}")
        
        print("\n" + "-" * 60)
        time.sleep(2)
    
    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN DE EXPERIMENTOS")
    print("=" * 60)
    
    exitosos = sum(1 for r in resultados if r['exito'])
    total = len(resultados)
    
    print(f"\nExperimentos exitosos: {exitosos}/{total}")
    print(f"Tasa de éxito: {(exitosos/total*100):.1f}%\n")
    
    for r in resultados:
        estado = "✅" if r['exito'] else "❌"
        print(f"{estado} {r['experimento']}")
        print(f"   Pedido ID: {r['pedido_id']}")
        print(f"   Esperado: {r['esperado']}, Obtenido: {r['obtenido']}")
        if r['items_faltantes'] > 0:
            print(f"   Items faltantes detectados: {r['items_faltantes']}")
        print()
    
    return exitosos == total

if __name__ == "__main__":
    if len(sys.argv) > 1:
        API_BASE_URL = sys.argv[1]
    
    if API_BASE_URL == "https://YOUR_API_GATEWAY_URL":
        print("⚠️  Por favor, actualiza API_BASE_URL en el script o pásalo como argumento:")
        print("   python experimento.py https://your-api-gateway-url.execute-api.region.amazonaws.com")
        sys.exit(1)
    
    exito = experimento_deteccion_fallos()
    
    if exito:
        print("\n🎉 ¡Todos los experimentos fueron exitosos!")
        print("   El sistema está detectando fallos correctamente el 100% de las veces.")
        sys.exit(0)
    else:
        print("\n⚠️  Algunos experimentos fallaron. Revisar configuración.")
        sys.exit(1)

