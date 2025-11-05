# Sistema de Gestión de Pedidos y Bodega - Detección de Fallos

Este proyecto implementa un sistema completo en AWS para la gestión de pedidos y bodega, con enfoque en la **detección del 100% de las veces** cuando no hay disponibilidad de items en un pedido.

## Arquitectura

El sistema está compuesto por los siguientes componentes principales:

1. **Validador de Disponibilidad**: Lambda function que compara items del pedido con disponibilidad en bodega
2. **Gestor de Anomalías**: Lambda function que decide el flujo según el resultado de la validación
3. **Sincronizador de Estado**: Lambda function que actualiza el estado de pedidos consistentes
4. **Emisor de Auditoría**: Lambda function que genera reportes de inconsistencia
5. **Bases de Datos RDS**: MySQL para almacenar pedidos, items y bodega
6. **SNS/SQS**: Para comunicación asíncrona y garantía de procesamiento
7. **CloudWatch**: Para monitoreo y logging
8. **API Gateway**: Para exponer endpoints REST

## Características de Detección de Fallos

El sistema garantiza la detección del 100% de los fallos mediante:

- **Dead Letter Queues (DLQ)**: Mensajes que fallan son enviados a DLQ para no perderse
- **Event Source Mapping**: SQS garantiza procesamiento de todos los mensajes
- **Validación exhaustiva**: Compara cada item del pedido con disponibilidad real
- **Logging detallado**: Todos los eventos se registran en CloudWatch
- **Alarmas de monitoreo**: Alertas cuando hay errores o mensajes en DLQ