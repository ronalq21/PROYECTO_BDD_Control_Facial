-- Usar la base de datos
USE vdm;

-- -Crear la tabla para almacenar la información de las personas
CREATE TABLE IF NOT EXISTS personas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre_completo VARCHAR(100) NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

#Crear la tabla para registrar la asistencia (entradas)
CREATE TABLE IF NOT EXISTS asistencia (
    id INT AUTO_INCREMENT PRIMARY KEY,
    persona_id INT,
    nombre_completo VARCHAR(100), -- Columna para el nombre, usada en el código
    fecha DATE NOT NULL,
    hora_entrada TIME NOT NULL,
    FOREIGN KEY (persona_id) REFERENCES personas (id)
);

-- Crear la tabla para registrar la asistencia (salidas)
CREATE TABLE IF NOT EXISTS asistencia_salida (
    id INT AUTO_INCREMENT PRIMARY KEY,
    persona_id INT NOT NULL,
    nombre_completo VARCHAR(255) NOT NULL,
    fecha DATE NOT NULL,
    hora_salida TIME NOT NULL,
    FOREIGN KEY (persona_id) REFERENCES personas (id),
    UNIQUE (persona_id, fecha) -- Asegura que solo haya un registro de salida por persona por día
);

-- Crear la tabla para los usuarios del sistema
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre_usuario VARCHAR(50) NOT NULL UNIQUE,
    contrasena VARCHAR(255) NOT NULL, -- Almacenar contraseñas hasheadas, nunca en texto plano
    contrasena_plana VARCHAR(255) NULL, -- Contraseña en texto plano (NO RECOMENDADO)
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    dni VARCHAR(20) NOT NULL UNIQUE,
    correo VARCHAR(100) NULL,
    celular VARCHAR(20) NULL
);

SELECT * from usuarios;

-- Ver los usuarios de la tabla (sin exponer la contraseña)
-- Es una buena práctica de seguridad no seleccionar la columna de la contraseña.
SELECT
    id,
    nombre_usuario,
    nombre,
    apellido,
    dni,
    correo,
    celular
FROM usuarios;

#borrar la tabla registros

use vdm;

DROP TABLE registros;