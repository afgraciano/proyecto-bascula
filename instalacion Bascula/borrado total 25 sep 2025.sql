-- MySQL dump 10.13  Distrib 8.0.43, for Win64 (x86_64)
--
-- Host: localhost    Database: bascula_silvotecnia
-- ------------------------------------------------------
-- Server version	8.0.43

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `cliente_interno`
--

DROP TABLE IF EXISTS `cliente_interno`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cliente_interno` (
  `id_cliente` int NOT NULL AUTO_INCREMENT,
  `tipo` varchar(100) DEFAULT NULL,
  `codigo_empresa` varchar(5) DEFAULT NULL,
  `nombre` varchar(100) DEFAULT NULL,
  `nit` varchar(50) DEFAULT NULL,
  `id_ingresado` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id_cliente`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cliente_interno`
--

LOCK TABLES `cliente_interno` WRITE;
/*!40000 ALTER TABLE `cliente_interno` DISABLE KEYS */;
/*!40000 ALTER TABLE `cliente_interno` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cliente_mensual`
--

DROP TABLE IF EXISTS `cliente_mensual`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cliente_mensual` (
  `id_cliente` int NOT NULL AUTO_INCREMENT,
  `tipo` varchar(100) DEFAULT NULL,
  `nombre` varchar(100) DEFAULT NULL,
  `nit` varchar(50) DEFAULT NULL,
  `id_ingresado` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id_cliente`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cliente_mensual`
--

LOCK TABLES `cliente_mensual` WRITE;
/*!40000 ALTER TABLE `cliente_mensual` DISABLE KEYS */;
/*!40000 ALTER TABLE `cliente_mensual` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cliente_tercero`
--

DROP TABLE IF EXISTS `cliente_tercero`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cliente_tercero` (
  `id_cliente` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) DEFAULT NULL,
  `cedula_nit` varchar(50) DEFAULT NULL,
  `correo_remision` varchar(100) DEFAULT NULL,
  `id_ingresado` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id_cliente`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cliente_tercero`
--

LOCK TABLES `cliente_tercero` WRITE;
/*!40000 ALTER TABLE `cliente_tercero` DISABLE KEYS */;
/*!40000 ALTER TABLE `cliente_tercero` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `desconexiones`
--

DROP TABLE IF EXISTS `desconexiones`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `desconexiones` (
  `id_desconexion` int NOT NULL AUTO_INCREMENT,
  `fecha_hora` datetime NOT NULL,
  `tipo_desconexion` varchar(50) DEFAULT NULL,
  `descripcion` varchar(100) DEFAULT NULL,
  `tiempo_desconexion` int DEFAULT '0',
  `id_autorizado` int DEFAULT NULL,
  PRIMARY KEY (`id_desconexion`),
  KEY `fk_desconexiones_autorizado` (`id_autorizado`),
  CONSTRAINT `fk_desconexiones_autorizado` FOREIGN KEY (`id_autorizado`) REFERENCES `personal_autorizado` (`id_autorizado`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `desconexiones`
--

LOCK TABLES `desconexiones` WRITE;
/*!40000 ALTER TABLE `desconexiones` DISABLE KEYS */;
/*!40000 ALTER TABLE `desconexiones` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `personal_autorizado`
--

DROP TABLE IF EXISTS `personal_autorizado`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `personal_autorizado` (
  `id_autorizado` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `login` varchar(100) NOT NULL,
  `password` varchar(20) NOT NULL,
  `cedula` varchar(20) NOT NULL,
  PRIMARY KEY (`id_autorizado`),
  UNIQUE KEY `login` (`login`),
  CONSTRAINT `personal_autorizado_chk_1` CHECK ((char_length(`password`) between 4 and 20))
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `personal_autorizado`
--

LOCK TABLES `personal_autorizado` WRITE;
/*!40000 ALTER TABLE `personal_autorizado` DISABLE KEYS */;
/*!40000 ALTER TABLE `personal_autorizado` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pesajes`
--

DROP TABLE IF EXISTS `pesajes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pesajes` (
  `id_pesaje` int NOT NULL AUTO_INCREMENT,
  `fecha_hora` datetime NOT NULL,
  `tipo_cliente` varchar(20) DEFAULT NULL,
  `peso_bruto` decimal(10,2) DEFAULT NULL,
  `peso_tara` decimal(10,2) DEFAULT NULL,
  `peso_neto` decimal(10,2) DEFAULT NULL,
  `placa` varchar(20) DEFAULT NULL,
  `id_cliente` int DEFAULT NULL,
  `id_autorizado` int DEFAULT NULL,
  `tipo_vehiculo` varchar(100) DEFAULT NULL,
  `comentarios` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id_pesaje`),
  KEY `fk_pesajes_autorizado` (`id_autorizado`),
  CONSTRAINT `fk_pesajes_autorizado` FOREIGN KEY (`id_autorizado`) REFERENCES `personal_autorizado` (`id_autorizado`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pesajes`
--

LOCK TABLES `pesajes` WRITE;
/*!40000 ALTER TABLE `pesajes` DISABLE KEYS */;
/*!40000 ALTER TABLE `pesajes` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-09-25 17:30:53
