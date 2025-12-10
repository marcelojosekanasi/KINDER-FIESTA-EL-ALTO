-- ================================================
-- KINDERFIESTA - SCRIPT DE BASE DE DATOS
-- ================================================

-- Crear la base de datos
CREATE DATABASE IF NOT EXISTS kinderfiesta
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

-- Usar la base de datos
USE kinderfiesta;

-- ================================================
-- TABLA: salones
-- Almacena la información de los salones infantiles
-- ================================================
CREATE TABLE IF NOT EXISTS salones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    phone VARCHAR(20),
    address VARCHAR(300) NOT NULL,
    locationCode VARCHAR(50),
    category VARCHAR(100),
    rating DECIMAL(2,1) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_name (name),
    INDEX idx_rating (rating)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ================================================
-- TABLA: horarios
-- Almacena los horarios de atención de los salones
-- ================================================
CREATE TABLE IF NOT EXISTS horarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    salon_id INT NOT NULL,
    dia ENUM('lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo') NOT NULL,
    hora_apertura TIME,
    hora_cierre TIME,
    cerrado BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (salon_id) REFERENCES salones(id) ON DELETE CASCADE,
    UNIQUE KEY unique_salon_dia (salon_id, dia)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ================================================
-- TABLA: reviews (comentarios y calificaciones)
-- Almacena los comentarios y calificaciones de usuarios
-- ================================================
CREATE TABLE IF NOT EXISTS reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    salon_id INT NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    comentario TEXT NOT NULL,
    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (salon_id) REFERENCES salones(id) ON DELETE CASCADE,
    INDEX idx_salon (salon_id),
    INDEX idx_fecha (fecha),
    INDEX idx_rating (rating)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ================================================
-- TABLA: administradores
-- Almacena las credenciales de los administradores
-- ================================================
CREATE TABLE IF NOT EXISTS administradores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    nombre VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ================================================
-- INSERTAR DATOS INICIALES
-- ================================================

-- Insertar administrador por defecto
INSERT INTO administradores (email, password, nombre) 
VALUES ('admin@kinderfiesta.com', '123456', 'Administrador Principal');

-- Insertar los 5 salones iniciales
INSERT INTO salones (id, name, phone, address, locationCode, category, rating) VALUES
(1, 'Salón Infantil MERLÍN', '65567153', 'Zona Elizardo, Alejandro Pérez, El Alto', 'FR88+66 El Alto', NULL, NULL),
(2, 'Salón de Eventos Infantiles Pequeño Gigante', '78915146', 'Av. 16 de Julio 500, El Alto', 'GR4F+7G El Alto', NULL, NULL),
(3, 'Salón ANGELITO', '78780824', 'Lado Promuyjer, Plaza Ballivián, Av. Pucararini 140, El Alto', 'GR6H+V3 El Alto', NULL, NULL),
(4, 'Salón Infantil Leoncito Valiente', '', 'Alvarez Plata 15, El Alto', '4R8Q+66 El Alto', 'Bufé para fiestas infantiles', 5.0),
(5, 'Salón de fiestas infantiles y familiares SAKURA FLOR DE CEREZO', '70551410', '0000, El Alto', '', NULL, NULL);

-- Insertar horarios para Salón Leoncito Valiente (id=4)
INSERT INTO horarios (salon_id, dia, hora_apertura, hora_cierre, cerrado) VALUES
(4, 'lunes', '08:00:00', '17:00:00', FALSE),
(4, 'martes', '08:00:00', '17:00:00', FALSE),
(4, 'miércoles', '08:00:00', '17:00:00', FALSE),
(4, 'jueves', '08:00:00', '17:00:00', FALSE),
(4, 'viernes', '08:00:00', '17:00:00', FALSE),
(4, 'sábado', NULL, NULL, TRUE),
(4, 'domingo', NULL, NULL, TRUE);

-- Insertar horarios para Salón SAKURA (id=5)
INSERT INTO horarios (salon_id, dia, hora_apertura, hora_cierre, cerrado) VALUES
(5, 'lunes', NULL, NULL, TRUE),
(5, 'martes', '14:00:00', '18:00:00', FALSE),
(5, 'miércoles', '14:00:00', '18:00:00', FALSE),
(5, 'jueves', '14:00:00', '18:00:00', FALSE),
(5, 'viernes', '14:00:00', '18:00:00', FALSE),
(5, 'sábado', '09:00:00', '16:00:00', FALSE),
(5, 'domingo', '14:00:00', '18:00:00', FALSE);

-- ================================================
-- VISTA: vista_salones_completa
-- Vista que muestra toda la información de los salones
-- ================================================
CREATE OR REPLACE VIEW vista_salones_completa AS
SELECT 
    s.id,
    s.name,
    s.phone,
    s.address,
    s.locationCode,
    s.category,
    s.rating,
    COUNT(DISTINCT r.id) as total_reviews,
    IFNULL(AVG(r.rating), 0) as rating_promedio
FROM salones s
LEFT JOIN reviews r ON s.id = r.salon_id
GROUP BY s.id, s.name, s.phone, s.address, s.locationCode, s.category, s.rating;

-- ================================================
-- PROCEDIMIENTO ALMACENADO: calcular_rating_promedio
-- Calcula y actualiza el rating promedio de un salón
-- ================================================
DELIMITER //

CREATE PROCEDURE calcular_rating_promedio(IN salon_id_param INT)
BEGIN
    DECLARE nuevo_rating DECIMAL(2,1);
    
    SELECT AVG(rating) INTO nuevo_rating
    FROM reviews
    WHERE salon_id = salon_id_param;
    
    UPDATE salones
    SET rating = nuevo_rating
    WHERE id = salon_id_param;
END //

DELIMITER ;

-- ================================================
-- TRIGGER: after_insert_review
-- Actualiza automáticamente el rating después de insertar un comentario
-- ================================================
DELIMITER //

CREATE TRIGGER after_insert_review
AFTER INSERT ON reviews
FOR EACH ROW
BEGIN
    CALL calcular_rating_promedio(NEW.salon_id);
END //

DELIMITER ;

-- ================================================
-- TRIGGER: after_delete_review
-- Actualiza automáticamente el rating después de eliminar un comentario
-- ================================================
DELIMITER //

CREATE TRIGGER after_delete_review
AFTER DELETE ON reviews
FOR EACH ROW
BEGIN
    CALL calcular_rating_promedio(OLD.salon_id);
END //

DELIMITER ;

-- ================================================
-- TRIGGER: after_update_review
-- Actualiza automáticamente el rating después de actualizar un comentario
-- ================================================
DELIMITER //

CREATE TRIGGER after_update_review
AFTER UPDATE ON reviews
FOR EACH ROW
BEGIN
    CALL calcular_rating_promedio(NEW.salon_id);
END //

DELIMITER ;

-- ================================================
-- CONSULTAS ÚTILES PARA VERIFICACIÓN
-- ================================================

-- Ver todos los salones con su información
SELECT * FROM vista_salones_completa;

-- Ver horarios de un salón específico
-- SELECT * FROM horarios WHERE salon_id = 4;

-- Ver reviews de un salón específico
-- SELECT * FROM reviews WHERE salon_id = 1 ORDER BY fecha DESC;

-- Ver estadísticas generales
-- SELECT 
--     COUNT(DISTINCT s.id) as total_salones,
--     COUNT(r.id) as total_reviews,
--     AVG(r.rating) as rating_promedio_general
-- FROM salones s
-- LEFT JOIN reviews r ON s.id = r.salon_id;