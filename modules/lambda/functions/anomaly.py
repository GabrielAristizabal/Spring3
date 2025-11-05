"""
Gestor de Anomalías
Este componente detecta si hay una inconsistencia y toma una decisión dependiendo del caso.
Si es consistente -> Sincronizador de Estado
Si no es consistente -> Emisor de Auditoría
"""
import json
import os
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sns_client = boto3.client('sns')
sqs_client = boto3.client('sqs')

def lambda_handler(event, context):
    """
    Handler principal de Lambda
    Procesa mensajes de SQS que contienen resultados de validación.
    """
    logger.info(f"Evento recibido: {json.dumps(event)}")
    
    resultados_procesados = []
    
    try:
        # Procesar cada mensaje del batch de SQS
        for record in event.get('Records', []):
            try:
                # Parsear mensaje SQS
                if 'body' in record:
                    # Si viene de SNS, hay un nested JSON
                    body = json.loads(record['body'])
                    if 'Message' in body:
                        # Mensaje de SNS
                        message_body = json.loads(body['Message'])
                    else:
                        message_body = body
                else:
                    message_body = record
                
                pedido_id = message_body.get('pedido_id')
                es_consistente = message_body.get('es_consistente', False)
                items_faltantes = message_body.get('items_faltantes', [])
                
                if not pedido_id:
                    logger.error("Mensaje sin pedido_id")
                    continue
                
                logger.info(f"Procesando anomalía para pedido {pedido_id}: consistente={es_consistente}")
                
                resultado_decision = {
                    'pedido_id': pedido_id,
                    'resultado_validacion': 'Consistente' if es_consistente else 'No consistente',
                    'es_consistente': es_consistente,
                    'items_faltantes': items_faltantes,
                    'timestamp': message_body.get('timestamp', '')
                }
                
                # Publicar en topic de anomalías con filtro
                anomaly_topic_arn = os.environ['ANOMALY_TOPIC_ARN']
                
                message_attributes = {
                    'pedido_id': {
                        'DataType': 'String',
                        'StringValue': str(pedido_id)
                    },
                    'resultado': {
                        'DataType': 'String',
                        'StringValue': 'Consistente' if es_consistente else 'No consistente'
                    }
                }
                
                sns_client.publish(
                    TopicArn=anomaly_topic_arn,
                    Message=json.dumps(resultado_decision),
                    Subject=f"Decisión Anomalía Pedido {pedido_id}",
                    MessageAttributes=message_attributes
                )
                
                logger.info(
                    f"Pedido {pedido_id}: Decisión enviada - "
                    f"{'Consistente -> Sincronizador' if es_consistente else 'No consistente -> Auditoría'}"
                )
                
                resultados_procesados.append(resultado_decision)
                
            except Exception as e:
                logger.error(f"Error procesando mensaje: {str(e)}", exc_info=True)
                raise
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'mensaje': 'Gestión de anomalías completada',
                'resultados': resultados_procesados
            })
        }
        
    except Exception as e:
        logger.error(f"Error fatal en lambda_handler: {str(e)}", exc_info=True)
        raise

