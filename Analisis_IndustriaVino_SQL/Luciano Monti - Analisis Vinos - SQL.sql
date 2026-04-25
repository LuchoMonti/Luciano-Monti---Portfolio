-- PASO CERO: BORRAR BASE DE DATOS EXISTENTE (PARA PRUEBAS)

DROP DATABASE IF EXISTS vinos_db;
-- Comentario: Elimina la BD si existe para permitir ejecución limpia desde cero.

-- BLOQUE 1: CREACIÓN DE LA ESTRUCTURA (DDL)

-- 1. Creación y selección de la base de datos
CREATE DATABASE IF NOT EXISTS vinos_db;
USE vinos_db;

-- 2. Creación de las tablas de dimensión
CREATE TABLE Paises (
    id_pais INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL UNIQUE -- Nombre único y no nulo para cada país.
);

CREATE TABLE Provincias (
    id_provincia INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(255) NULL, -- Se permite NULL temporalmente por si hay datos faltantes en origen.
    id_pais INT NULL, -- Se permite NULL por si no se encuentra el país asociado.
    FOREIGN KEY (id_pais) REFERENCES Paises(id_pais)
);

CREATE TABLE Regiones (
    id_region INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(255) NULL, -- Se permite NULL temporalmente.
    id_provincia INT NULL, -- Se permite NULL por si no se encuentra la provincia asociada.
    FOREIGN KEY (id_provincia) REFERENCES Provincias(id_provincia)
);

CREATE TABLE Variedades (
    id_variedad INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL UNIQUE -- Nombre único y no nulo para cada variedad.
);

CREATE TABLE Catadores (
    id_catador INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(255) NULL, -- Se permite NULL temporalmente.
    twitter_handle VARCHAR(255)
);

CREATE TABLE Bodegas (
    id_bodega INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(255) NULL -- Se permite NULL temporalmente.
);

-- 3. Creación de la tabla de hechos (tabla central que almacena cada reseña y conecta las dimensiones)
CREATE TABLE Reseñas (
    id_reseña INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(255),
    descripcion TEXT,
    puntos INT NULL,
    precio DECIMAL(10,2) NULL,
    designacion VARCHAR(255),
    id_region INT NULL,
    id_variedad INT NULL,
    id_catador INT NULL,
    id_bodega INT NULL,
    FOREIGN KEY (id_region) REFERENCES Regiones(id_region),
    FOREIGN KEY (id_variedad) REFERENCES Variedades(id_variedad),
    FOREIGN KEY (id_catador) REFERENCES Catadores(id_catador),
    FOREIGN KEY (id_bodega) REFERENCES Bodegas(id_bodega)
);

-- BLOQUE 2: CARGA DE DATOS (ETL - DML)

-- 4. Creación de la tabla de preparación (carga inicial con tipos de datos flexibles para evitar errores)
DROP TABLE IF EXISTS preparacion_reseñas;
CREATE TABLE preparacion_reseñas (
    id VARCHAR(50), country VARCHAR(255), description TEXT, designation VARCHAR(255),
    points VARCHAR(50), price VARCHAR(50), province VARCHAR(255), region_1 VARCHAR(255),
    region_2 VARCHAR(255), taster_name VARCHAR(255), taster_twitter_handle VARCHAR(255),
    title VARCHAR(255), variety VARCHAR(255), winery VARCHAR(255)
);

-- 5. Carga del CSV a la tabla de preparación
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/winemag-data-130k-v2.csv' -- Ajustar ruta al archivo
INTO TABLE preparacion_reseñas
CHARACTER SET latin1 FIELDS TERMINATED BY ';'
ENCLOSED BY '"' LINES TERMINATED BY '\r\n' IGNORE 1 ROWS;

-- 6. Limpieza de Datos corruptos en preparación
SET SQL_SAFE_UPDATES = 0;
DELETE FROM preparacion_reseñas
WHERE id IS NULL OR id = '' OR id REGEXP '[^0-9]';
SET SQL_SAFE_UPDATES = 1;

-- BLOQUE 3: ALIMENTAR TABLAS FINALES DESDE PREPARACIÓN (ETL - DML)

-- 7. Alimentar tabla Paises
INSERT IGNORE INTO Paises (nombre)
SELECT DISTINCT TRIM(UPPER(pr.country))
FROM preparacion_reseñas pr
WHERE pr.country IS NOT NULL AND TRIM(pr.country) <> '';

-- 8. Alimentar tabla Provincias
INSERT IGNORE INTO Provincias (nombre, id_pais)
SELECT DISTINCT TRIM(pr.province), p.id_pais
FROM preparacion_reseñas pr
JOIN Paises p ON TRIM(UPPER(pr.country)) = p.nombre
WHERE pr.province IS NOT NULL AND TRIM(pr.province) <> '';

-- 9. Alimentar tabla Regiones
INSERT IGNORE INTO Regiones (nombre, id_provincia)
SELECT DISTINCT TRIM(pr.region_1), prov.id_provincia 
FROM preparacion_reseñas pr
JOIN Provincias prov ON TRIM(pr.province) = prov.nombre
JOIN Paises pa ON TRIM(UPPER(pr.country)) = pa.nombre AND prov.id_pais = pa.id_pais
WHERE pr.region_1 IS NOT NULL AND TRIM(pr.region_1) <> '';

-- 10. Alimentar tabla Variedades
INSERT IGNORE INTO Variedades (nombre)
SELECT DISTINCT TRIM(pr.variety)
FROM preparacion_reseñas pr
WHERE pr.variety IS NOT NULL AND TRIM(pr.variety) <> '';

-- 11. Alimentar tabla Catadores
INSERT IGNORE INTO Catadores (nombre, twitter_handle)
SELECT DISTINCT TRIM(pr.taster_name), TRIM(pr.taster_twitter_handle)
FROM preparacion_reseñas pr
WHERE pr.taster_name IS NOT NULL AND TRIM(pr.taster_name) <> '';

-- 12. Alimentar tabla Bodegas
INSERT IGNORE INTO Bodegas (nombre)
SELECT DISTINCT TRIM(pr.winery)
FROM preparacion_reseñas pr
WHERE pr.winery IS NOT NULL AND TRIM(pr.winery) <> '';

-- 13. Alimentar Tabla de Hechos Resenas
INSERT INTO Reseñas (titulo, descripcion, puntos, precio, designacion, id_region, id_variedad, id_catador, id_bodega)
SELECT
    pr.title, pr.description,
    CASE WHEN pr.points REGEXP '^[0-9]+$' THEN CAST(pr.points AS UNSIGNED) ELSE NULL END AS puntos,
    CASE WHEN pr.price REGEXP '^[0-9]+(\\.[0-9]+)?$' THEN CAST(pr.price AS DECIMAL(10,2)) ELSE NULL END AS precio,
    pr.designation, reg.id_region, var.id_variedad, cat.id_catador, bod.id_bodega
FROM
    preparacion_reseñas pr
LEFT JOIN Paises pais ON TRIM(UPPER(pr.country)) = pais.nombre
LEFT JOIN Provincias prov ON TRIM(pr.province) = prov.nombre AND prov.id_pais = pais.id_pais
LEFT JOIN Regiones reg ON TRIM(pr.region_1) = reg.nombre AND reg.id_provincia = prov.id_provincia
LEFT JOIN Variedades var ON TRIM(pr.variety) = var.nombre
LEFT JOIN Catadores cat ON TRIM(pr.taster_name) = cat.nombre
LEFT JOIN Bodegas bod ON TRIM(pr.winery) = bod.nombre;

-- BLOQUE 4: CONSULTAS SQL AVANZADAS

-- Consulta 1: Cantidad de vinos por país (Top 10)
SELECT p.nombre AS Pais, COUNT(r.id_reseña) AS CantidadReseñas
FROM Reseñas r
JOIN Regiones reg ON r.id_region = reg.id_region
JOIN Provincias prov ON reg.id_provincia = prov.id_provincia
JOIN Paises p ON prov.id_pais = p.id_pais
GROUP BY p.nombre
ORDER BY CantidadReseñas DESC
LIMIT 10;

-- Consulta 2: Variedades más comunes en una región específica (Ej: Napa Valley - Top 5)
SELECT 
    v.nombre AS Variedad, 
    COUNT(r.id_reseña) AS CantidadReseñas
FROM Reseñas r
JOIN Variedades v ON r.id_variedad = v.id_variedad 
JOIN Regiones reg ON r.id_region = reg.id_region
WHERE reg.nombre = 'Napa Valley' 
GROUP BY v.nombre
ORDER BY CantidadReseñas DESC
LIMIT 5;

-- Consulta 3: Precio promedio por punto de calificación en un país específico (Ej: US)
SELECT 
    r.puntos AS Puntuacion, 
    FORMAT(AVG(r.precio), 2) AS PrecioPromedio_USD
FROM Reseñas r
JOIN Regiones reg ON r.id_region = reg.id_region 
JOIN Provincias prov ON reg.id_provincia = prov.id_provincia 
JOIN Paises p ON prov.id_pais = p.id_pais 
WHERE p.nombre = 'US'
  AND r.precio IS NOT NULL
GROUP BY r.puntos
ORDER BY r.puntos ASC;

-- Consulta 4: Catadores que reseñan los vinos más caros en promedio (Top 5)
SELECT 
    c.nombre AS Catador,
    FORMAT(AVG(r.precio), 2) AS PrecioPromedioReseñado_USD,
    COUNT(r.id_reseña) AS CantidadReseñas
FROM Reseñas r
JOIN Catadores c ON r.id_catador = c.id_catador
WHERE r.precio IS NOT NULL
GROUP BY c.nombre
ORDER BY AVG(r.precio) DESC
LIMIT 5;


-- BLOQUE 5: ANÁLISIS MULTIDIMENSIONAL

-- Consulta 5: Variedades más reseñadas en Argentina (Top 5)
SELECT 
    v.nombre AS Variedad,
    COUNT(r.id_reseña) AS CantidadReseñas
FROM Reseñas r
JOIN Variedades v ON r.id_variedad = v.id_variedad
JOIN Regiones reg ON r.id_region = reg.id_region
JOIN Provincias prov ON reg.id_provincia = prov.id_provincia
JOIN Paises p ON prov.id_pais = p.id_pais
WHERE p.nombre = 'ARGENTINA'
GROUP BY v.nombre
ORDER BY CantidadReseñas DESC
LIMIT 5;

-- Consulta 6: Bodegas Argentinas con mayor de Malbecs reseñados
SELECT
    b.nombre AS Bodega,
    COUNT(DISTINCT v.nombre) AS CantidadVariedadesMalbec
FROM Reseñas r
JOIN Bodegas b ON r.id_bodega = b.id_bodega
JOIN Variedades v ON r.id_variedad = v.id_variedad
JOIN Regiones reg ON r.id_region = reg.id_region
JOIN Provincias prov ON reg.id_provincia = prov.id_provincia
JOIN Paises p ON prov.id_pais = p.id_pais
WHERE p.nombre = 'ARGENTINA'
  AND v.nombre LIKE '%Malbec%'
GROUP BY b.nombre
ORDER BY CantidadVariedadesMalbec DESC
LIMIT 5;

-- Consulta 7: Malbec mejor puntuado de cada bodega Argentina y su precio
WITH MejoresMalbecsPorBodega AS ( 
    SELECT
        b.nombre AS Bodega,
        r.titulo AS TituloVino,
        r.puntos AS Puntuacion,
        r.precio AS Precio,
        -- Asigna Rank 1 a los vinos con mayor puntaje de de cada bodega
        RANK() OVER (PARTITION BY b.nombre ORDER BY r.puntos DESC) as ranking_por_bodega
    FROM Reseñas r
    JOIN Bodegas b ON r.id_bodega = b.id_bodega
    JOIN Variedades v ON r.id_variedad = v.id_variedad
    JOIN Regiones reg ON r.id_region = reg.id_region
    JOIN Provincias prov ON reg.id_provincia = prov.id_provincia
    JOIN Paises p ON prov.id_pais = p.id_pais
    WHERE
        p.nombre = 'ARGENTINA'
        AND v.nombre LIKE '%Malbec%'
        AND r.puntos IS NOT NULL
        AND r.precio IS NOT NULL
)
SELECT
    Bodega,
    TituloVino,
    Puntuacion,
    FORMAT(Precio, 2) AS Precio_USD
FROM MejoresMalbecsPorBodega
WHERE ranking_por_bodega = 1
ORDER BY Bodega, Puntuacion DESC, Precio DESC;