-- Script de inicialización de base de datos
-- Este script crea las tablas necesarias para el sistema de pedidos y bodega

-- Base de datos principal (order_management)
USE order_management;

-- Tabla de pedidos
CREATE TABLE IF NOT EXISTS pedidos (
    pedido_id INT AUTO_INCREMENT PRIMARY KEY,
    estado VARCHAR(50) NOT NULL DEFAULT 'pendiente',
    fecha_creacion DATETIME NOT NULL,
    fecha_validacion DATETIME NULL,
    fecha_fallo DATETIME NULL,
    ultima_actualizacion DATETIME NOT NULL,
    INDEX idx_estado (estado),
    INDEX idx_fecha_creacion (fecha_creacion)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Tabla de items del pedido
CREATE TABLE IF NOT EXISTS pedido_items (
    pedido_item_id INT AUTO_INCREMENT PRIMARY KEY,
    pedido_id INT NOT NULL,
    item_id INT NOT NULL,
    cantidad_solicitada INT NOT NULL,
    nombre_item VARCHAR(255) NULL,
    FOREIGN KEY (pedido_id) REFERENCES pedidos(pedido_id) ON DELETE CASCADE,
    INDEX idx_pedido_id (pedido_id),
    INDEX idx_item_id (item_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Tabla de reportes de inconsistencia
CREATE TABLE IF NOT EXISTS reportes_inconsistencia (
    reporte_id INT AUTO_INCREMENT PRIMARY KEY,
    pedido_id INT NOT NULL,
    items_faltantes JSON NOT NULL,
    fecha_deteccion DATETIME NOT NULL,
    estado VARCHAR(50) NOT NULL DEFAULT 'pendiente',
    FOREIGN KEY (pedido_id) REFERENCES pedidos(pedido_id) ON DELETE CASCADE,
    INDEX idx_pedido_id (pedido_id),
    INDEX idx_fecha_deteccion (fecha_deteccion)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Base de datos de persistencia (persistence)
USE persistence;

-- Tabla de items en bodega
CREATE TABLE IF NOT EXISTS bodega_items (
    item_id INT PRIMARY KEY,
    nombre_item VARCHAR(255) NOT NULL,
    cantidad_disponible INT NOT NULL DEFAULT 0,
    cantidad_reservada INT NOT NULL DEFAULT 0,
    ultima_actualizacion DATETIME NOT NULL,
    INDEX idx_cantidad_disponible (cantidad_disponible)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Insertar algunos items de ejemplo para pruebas
INSERT INTO bodega_items (item_id, nombre_item, cantidad_disponible, cantidad_reservada, ultima_actualizacion)
VALUES 
    (1, 'Item A', 100, 0, NOW()),
    (2, 'Item B', 50, 0, NOW()),
    (3, 'Item C', 75, 0, NOW()),
    (4, 'Item D', 200, 0, NOW()),
    (5, 'Item E', 30, 0, NOW())
ON DUPLICATE KEY UPDATE 
    ultima_actualizacion = NOW();

