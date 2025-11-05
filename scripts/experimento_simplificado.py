#!/usr/bin/env python3
"""
Script de experimento simplificado - conecta directamente a RDS
No requiere API Gateway ni Lambda
"""
import json
import sys
import subprocess
import os

# Configuración desde variables de entorno o argumentos
def get_db_config():
    """Obtiene configuración de base de datos"""
    # Intentar desde variables de entorno primero
    main_db_endpoint = os.environ.get('MAIN_DB_ENDPOINT')
    persistence_db_endpoint = os.environ.get('PERSISTENCE_DB_ENDPOINT')
    db_username = os.environ.get('DB_USERNAME', 'admin')
    db_password = os.environ.get('DB_PASSWORD')
    
    if not all([main_db_endpoint, persistence_db_endpoint, db_password]):
        print("❌ Error: Configura las siguientes variables de entorno:")
        print("   MAIN_DB_ENDPOINT")
        print("   PERSISTENCE_DB_ENDPOINT")
        print("   DB_PASSWORD")
        print("   DB_USERNAME (opcional, default: admin)")
        print("\nO pásalas como argumentos:")
        print("   python experimento_simplificado.py <main_db_endpoint> <persistence_db_endpoint> <db_username> <db_password>")
        sys.exit(1)
    
    return main_db_endpoint, persistence_db_endpoint, db_username, db_password

def crear_pedido(main_db_endpoint, db_username, db_password, items):
    """Crea un pedido usando el script directo"""
    items_json = json.dumps(items)
    cmd = [
        'python3', 'scripts/crear_pedido_directo.py',
        main_db_endpoint,
        'order_management',
        db_username,
        db_password,
        items_json
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creando pedido: {e.stderr}")
        return None

def verificar_consistencia(main_db_endpoint, persistence_db_endpoint, db_username, db_password, pedido_id):
    """Verifica consistencia usando el script directo"""
    cmd = [
        'python3', 'scripts/verificar_consistencia_directo.py',
        main_db_endpoint,
        'order_management',
        persistence_db_endpoint,
        'persistence',
        db_username,
        db_password,
        str(pedido_id)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error verificando consistencia: {e.stderr}")
        return None

def experimento_deteccion_fallos():
    """Ejecuta experimentos para probar la detección de fallos"""
    print("=" * 60)
    print("EXPERIMENTO SIMPLIFICADO: Detección de Fallos")
    print("=" * 60)
    
    # Obtener configuración
    if len(sys.argv) >= 5:
        main_db_endpoint = sys.argv[1]
        persistence_db_endpoint = sys.argv[2]
        db_username = sys.argv[3]
        db_password = sys.argv[4]
    else:
        main_db_endpoint, persistence_db_endpoint, db_username, db_password = get_db_config()
    
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
                {"item_id": 1, "cantidad": 150, "nombre_item": "Item A"},
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
                {"item_id": 1, "cantidad": 150, "nombre_item": "Item A"},
                {"item_id": 2, "cantidad": 100, "nombre_item": "Item B"},
                {"item_id": 999, "cantidad": 10, "nombre_item": "Item No Existente"}
            ],
            "esperado": "no_consistente"
        },
        {
            "nombre": "Experimento 5: Pedido exacto",
            "items": [
                {"item_id": 5, "cantidad": 30, "nombre_item": "Item E"}
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
        print(f"\n📦 Creando pedido...")
        resultado_creacion = crear_pedido(main_db_endpoint, db_username, db_password, experimento['items'])
        
        if not resultado_creacion or 'pedido_id' not in resultado_creacion:
            print("⚠️  No se pudo crear el pedido, saltando experimento...")
            continue
        
        pedido_id = resultado_creacion['pedido_id']
        print(f"✅ Pedido creado: ID {pedido_id}")
        
        # Verificar consistencia
        print(f"\n🔍 Verificando consistencia...")
        resultado = verificar_consistencia(main_db_endpoint, persistence_db_endpoint, 
                                          db_username, db_password, pedido_id)
        
        if resultado and 'error' not in resultado:
            es_consistente = resultado.get('es_consistente', False)
            items_faltantes = resultado.get('items_faltantes', [])
            
            esperado_consistente = experimento['esperado'] == 'consistente'
            exito = (es_consistente == esperado_consistente)
            
            if es_consistente:
                print(f"✅ Pedido CONSISTENTE")
            else:
                print(f"❌ Pedido NO CONSISTENTE - {len(items_faltantes)} items faltantes")
                for item in items_faltantes:
                    print(f"   - {item['nombre_item']}: {item['razon']}")
            
            resultados.append({
                'experimento': experimento['nombre'],
                'pedido_id': pedido_id,
                'esperado': experimento['esperado'],
                'obtenido': 'consistente' if es_consistente else 'no_consistente',
                'exito': exito,
                'items_faltantes': len(items_faltantes)
            })
            
            if exito:
                print(f"\n✅ EXPERIMENTO EXITOSO")
            else:
                print(f"\n❌ EXPERIMENTO FALLIDO")
        else:
            print(f"❌ Error: {resultado.get('error', 'Desconocido')}")
        
        print("\n" + "-" * 60)
    
    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN DE EXPERIMENTOS")
    print("=" * 60)
    
    exitosos = sum(1 for r in resultados if r['exito'])
    total = len(resultados)
    
    if total > 0:
        print(f"\nExperimentos exitosos: {exitosos}/{total}")
        print(f"Tasa de éxito: {(exitosos/total*100):.1f}%\n")
        
        for r in resultados:
            estado = "✅" if r['exito'] else "❌"
            print(f"{estado} {r['experimento']}")
            print(f"   Pedido ID: {r['pedido_id']}")
            print(f"   Esperado: {r['esperado']}, Obtenido: {r['obtenido']}")
            if r['items_faltantes'] > 0:
                print(f"   Items faltantes: {r['items_faltantes']}")
            print()
        
        if exitosos == total:
            print("\n🎉 ¡Todos los experimentos fueron exitosos!")
            print("   El sistema está detectando fallos correctamente el 100% de las veces.")
            return 0
        else:
            print("\n⚠️  Algunos experimentos fallaron.")
            return 1
    else:
        print("\n❌ No se completó ningún experimento.")
        return 1

if __name__ == "__main__":
    sys.exit(experimento_deteccion_fallos())

