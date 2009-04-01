-- MySQL dump 10.11
--
-- Host: localhost    Database: ieeetags
-- ------------------------------------------------------
-- Server version	5.0.51a-community-nt-log

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `auth_group` (
  `id` int(11) NOT NULL auto_increment,
  `name` varchar(80) collate utf8_unicode_ci NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `auth_group_permissions` (
  `id` int(11) NOT NULL auto_increment,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `group_id` (`group_id`,`permission_id`),
  KEY `permission_id_refs_id_5886d21f` (`permission_id`),
  CONSTRAINT `permission_id_refs_id_5886d21f` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `group_id_refs_id_3cea63fe` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_message`
--

DROP TABLE IF EXISTS `auth_message`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `auth_message` (
  `id` int(11) NOT NULL auto_increment,
  `user_id` int(11) NOT NULL,
  `message` longtext collate utf8_unicode_ci NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `auth_message_user_id` (`user_id`),
  CONSTRAINT `user_id_refs_id_650f49a6` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `auth_message`
--

LOCK TABLES `auth_message` WRITE;
/*!40000 ALTER TABLE `auth_message` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_message` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `auth_permission` (
  `id` int(11) NOT NULL auto_increment,
  `name` varchar(50) collate utf8_unicode_ci NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) collate utf8_unicode_ci NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `content_type_id` (`content_type_id`,`codename`),
  KEY `auth_permission_content_type_id` (`content_type_id`),
  CONSTRAINT `content_type_id_refs_id_728de91f` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=49 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add log entry',1,'add_logentry'),(2,'Can change log entry',1,'change_logentry'),(3,'Can delete log entry',1,'delete_logentry'),(4,'Can add permission',2,'add_permission'),(5,'Can change permission',2,'change_permission'),(6,'Can delete permission',2,'delete_permission'),(7,'Can add group',3,'add_group'),(8,'Can change group',3,'change_group'),(9,'Can delete group',3,'delete_group'),(10,'Can add user',4,'add_user'),(11,'Can change user',4,'change_user'),(12,'Can delete user',4,'delete_user'),(13,'Can add message',5,'add_message'),(14,'Can change message',5,'change_message'),(15,'Can delete message',5,'delete_message'),(16,'Can add content type',6,'add_contenttype'),(17,'Can change content type',6,'change_contenttype'),(18,'Can delete content type',6,'delete_contenttype'),(19,'Can add session',7,'add_session'),(20,'Can change session',7,'change_session'),(21,'Can delete session',7,'delete_session'),(22,'Can add site',8,'add_site'),(23,'Can change site',8,'change_site'),(24,'Can delete site',8,'delete_site'),(25,'Can add node type',9,'add_nodetype'),(26,'Can change node type',9,'change_nodetype'),(27,'Can delete node type',9,'delete_nodetype'),(28,'Can add node',10,'add_node'),(29,'Can change node',10,'change_node'),(30,'Can delete node',10,'delete_node'),(31,'Can add society',11,'add_society'),(32,'Can change society',11,'change_society'),(33,'Can delete society',11,'delete_society'),(34,'Can add resource type',12,'add_resourcetype'),(35,'Can change resource type',12,'change_resourcetype'),(36,'Can delete resource type',12,'delete_resourcetype'),(37,'Can add resource',13,'add_resource'),(38,'Can change resource',13,'change_resource'),(39,'Can delete resource',13,'delete_resource'),(40,'Can add filter',14,'add_filter'),(41,'Can change filter',14,'change_filter'),(42,'Can delete filter',14,'delete_filter'),(43,'Can add permission',15,'add_permission'),(44,'Can change permission',15,'change_permission'),(45,'Can delete permission',15,'delete_permission'),(46,'Can add profile',16,'add_profile'),(47,'Can change profile',16,'change_profile'),(48,'Can delete profile',16,'delete_profile');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user`
--

DROP TABLE IF EXISTS `auth_user`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `auth_user` (
  `id` int(11) NOT NULL auto_increment,
  `username` varchar(30) collate utf8_unicode_ci NOT NULL,
  `first_name` varchar(30) collate utf8_unicode_ci NOT NULL,
  `last_name` varchar(30) collate utf8_unicode_ci NOT NULL,
  `email` varchar(75) collate utf8_unicode_ci NOT NULL,
  `password` varchar(128) collate utf8_unicode_ci NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `last_login` datetime NOT NULL,
  `date_joined` datetime NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `auth_user`
--

LOCK TABLES `auth_user` WRITE;
/*!40000 ALTER TABLE `auth_user` DISABLE KEYS */;
INSERT INTO `auth_user` VALUES (1,'admin','Admin','','admin@systemicist.com','sha1$7524e$bb4a8fcc308e0e8a4451ce4428ecd7d487985fd5',1,1,1,'2009-04-01 16:38:13','2009-03-11 14:39:39'),(2,'soc','Society','','','sha1$314b1$ea2b7ef38fb49c42cc7ed529715aaeec99171a1a',1,1,0,'2009-03-11 14:41:06','2009-03-11 14:41:06'),(3,'multisoc','Society','(Multiple)','','sha1$5333e$0cf657779a783225185a94099d2086de360518a0',1,1,0,'2009-03-17 15:37:12','2009-03-17 15:37:12');
/*!40000 ALTER TABLE `auth_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_groups`
--

DROP TABLE IF EXISTS `auth_user_groups`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `auth_user_groups` (
  `id` int(11) NOT NULL auto_increment,
  `user_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `user_id` (`user_id`,`group_id`),
  KEY `group_id_refs_id_f116770` (`group_id`),
  CONSTRAINT `group_id_refs_id_f116770` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `user_id_refs_id_7ceef80f` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `auth_user_groups`
--

LOCK TABLES `auth_user_groups` WRITE;
/*!40000 ALTER TABLE `auth_user_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_user_permissions`
--

DROP TABLE IF EXISTS `auth_user_user_permissions`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `auth_user_user_permissions` (
  `id` int(11) NOT NULL auto_increment,
  `user_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `user_id` (`user_id`,`permission_id`),
  KEY `permission_id_refs_id_67e79cb` (`permission_id`),
  CONSTRAINT `permission_id_refs_id_67e79cb` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `user_id_refs_id_dfbab7d` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `auth_user_user_permissions`
--

LOCK TABLES `auth_user_user_permissions` WRITE;
/*!40000 ALTER TABLE `auth_user_user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `django_admin_log` (
  `id` int(11) NOT NULL auto_increment,
  `action_time` datetime NOT NULL,
  `user_id` int(11) NOT NULL,
  `content_type_id` int(11) default NULL,
  `object_id` longtext collate utf8_unicode_ci,
  `object_repr` varchar(200) collate utf8_unicode_ci NOT NULL,
  `action_flag` smallint(5) unsigned NOT NULL,
  `change_message` longtext collate utf8_unicode_ci NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `django_admin_log_user_id` (`user_id`),
  KEY `django_admin_log_content_type_id` (`content_type_id`),
  CONSTRAINT `content_type_id_refs_id_288599e6` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `user_id_refs_id_c8665aa` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `django_content_type` (
  `id` int(11) NOT NULL auto_increment,
  `name` varchar(100) collate utf8_unicode_ci NOT NULL,
  `app_label` varchar(100) collate utf8_unicode_ci NOT NULL,
  `model` varchar(100) collate utf8_unicode_ci NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `app_label` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (1,'log entry','admin','logentry'),(2,'permission','auth','permission'),(3,'group','auth','group'),(4,'user','auth','user'),(5,'message','auth','message'),(6,'content type','contenttypes','contenttype'),(7,'session','sessions','session'),(8,'site','sites','site'),(9,'node type','ieeetags','nodetype'),(10,'node','ieeetags','node'),(11,'society','ieeetags','society'),(12,'resource type','ieeetags','resourcetype'),(13,'resource','ieeetags','resource'),(14,'filter','ieeetags','filter'),(15,'permission','ieeetags','permission'),(16,'profile','ieeetags','profile');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `django_session` (
  `session_key` varchar(40) collate utf8_unicode_ci NOT NULL,
  `session_data` longtext collate utf8_unicode_ci NOT NULL,
  `expire_date` datetime NOT NULL,
  PRIMARY KEY  (`session_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
INSERT INTO `django_session` VALUES ('45a740653fbb850c90c1ccbb747142f6','gAJ9cQEoVRJfYXV0aF91c2VyX2JhY2tlbmRxAlUpZGphbmdvLmNvbnRyaWIuYXV0aC5iYWNrZW5k\ncy5Nb2RlbEJhY2tlbmRxA1UNX2F1dGhfdXNlcl9pZHEEigEBdS5mMDhlNmU4NGJkMDgyOTEwN2Uz\nNmY2OGNiMDgxYzY5OQ==\n','2009-03-31 15:36:21'),('7a87f60a5003acb20ab624e21d0a6953','gAJ9cQEoVRJfYXV0aF91c2VyX2JhY2tlbmRxAlUpZGphbmdvLmNvbnRyaWIuYXV0aC5iYWNrZW5k\ncy5Nb2RlbEJhY2tlbmRxA1UNX2F1dGhfdXNlcl9pZHEEigEBdS5mMDhlNmU4NGJkMDgyOTEwN2Uz\nNmY2OGNiMDgxYzY5OQ==\n','2009-04-15 16:38:13');
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_site`
--

DROP TABLE IF EXISTS `django_site`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `django_site` (
  `id` int(11) NOT NULL auto_increment,
  `domain` varchar(100) collate utf8_unicode_ci NOT NULL,
  `name` varchar(50) collate utf8_unicode_ci NOT NULL,
  PRIMARY KEY  (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `django_site`
--

LOCK TABLES `django_site` WRITE;
/*!40000 ALTER TABLE `django_site` DISABLE KEYS */;
INSERT INTO `django_site` VALUES (1,'example.com','example.com');
/*!40000 ALTER TABLE `django_site` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ieeetags_filter`
--

DROP TABLE IF EXISTS `ieeetags_filter`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `ieeetags_filter` (
  `id` int(11) NOT NULL auto_increment,
  `name` varchar(50) collate utf8_unicode_ci NOT NULL,
  `value` varchar(500) collate utf8_unicode_ci NOT NULL,
  PRIMARY KEY  (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `ieeetags_filter`
--

LOCK TABLES `ieeetags_filter` WRITE;
/*!40000 ALTER TABLE `ieeetags_filter` DISABLE KEYS */;
INSERT INTO `ieeetags_filter` VALUES (1,'Emerging Technologies','emerging_technologies'),(2,'Foundation Technologies','foundation_technologies'),(3,'Hot Topics','hot_topics'),(4,'Market Areas','market_areas'),(5,'Publishing Ecosystem','publishing_ecosystem'),(6,'Players','players'),(7,'Area 1','area_1');
/*!40000 ALTER TABLE `ieeetags_filter` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ieeetags_node`
--

DROP TABLE IF EXISTS `ieeetags_node`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `ieeetags_node` (
  `id` int(11) NOT NULL auto_increment,
  `name` varchar(500) collate utf8_unicode_ci NOT NULL,
  `parent_id` int(11) default NULL,
  `node_type_id` int(11) NOT NULL,
  `num_related_tags` int(11) default NULL,
  `num_resources` int(11) default NULL,
  `num_related_sectors` int(11) default NULL,
  PRIMARY KEY  (`id`),
  KEY `ieeetags_node_parent_id` (`parent_id`),
  KEY `ieeetags_node_node_type_id` (`node_type_id`),
  CONSTRAINT `node_type_id_refs_id_652d089` FOREIGN KEY (`node_type_id`) REFERENCES `ieeetags_nodetype` (`id`),
  CONSTRAINT `parent_id_refs_id_aadfc7d` FOREIGN KEY (`parent_id`) REFERENCES `ieeetags_node` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=352 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `ieeetags_node`
--

LOCK TABLES `ieeetags_node` WRITE;
/*!40000 ALTER TABLE `ieeetags_node` DISABLE KEYS */;
INSERT INTO `ieeetags_node` VALUES (1,'IEEE',NULL,1,NULL,NULL,NULL),(2,'Agriculture',1,2,NULL,NULL,NULL),(3,'Communications',1,2,NULL,NULL,NULL),(4,'Computing & IT',1,2,NULL,NULL,NULL),(5,'Critical Infrastructure',1,2,NULL,NULL,NULL),(6,'Defense',1,2,NULL,NULL,NULL),(7,'Education',1,2,NULL,NULL,NULL),(8,'Energy',1,2,NULL,NULL,NULL),(9,'Entertainment',1,2,NULL,NULL,NULL),(10,'Environment',1,2,NULL,NULL,NULL),(11,'Financial Services',1,2,NULL,NULL,NULL),(12,'Healthcare',1,2,NULL,NULL,NULL),(13,'Manufacturing & Devices',1,2,NULL,NULL,NULL),(14,'Retail',1,2,NULL,NULL,NULL),(15,'Transportation',1,2,NULL,NULL,NULL),(240,'Newspapers',9,3,0,0,0),(241,'Newspapers',3,3,0,0,0),(242,'Newspapers',4,3,0,0,0),(243,'Newspapers',13,3,0,0,0),(244,'Magazines',9,3,0,0,0),(245,'Magazines',3,3,0,0,0),(246,'Magazines',4,3,0,0,0),(247,'Magazines',13,3,0,0,0),(248,'Books',9,3,0,0,0),(249,'Books',3,3,0,0,0),(250,'Books',4,3,0,0,0),(251,'Books',13,3,0,0,0),(252,'Leaflet',9,3,0,0,0),(253,'Leaflet',3,3,0,0,0),(254,'Leaflet',4,3,0,0,0),(255,'Leaflet',13,3,0,0,0),(256,'Billboards',9,3,0,0,0),(257,'Billboards',3,3,0,0,0),(258,'Billboards',4,3,0,0,0),(259,'Billboards',13,3,0,0,0),(260,'Electronic Publishers',9,3,0,0,0),(261,'Electronic Publishers',3,3,0,0,0),(262,'Electronic Publishers',4,3,0,0,0),(263,'Electronic Publishers',13,3,0,0,0),(264,'Search Engine',9,3,0,0,0),(265,'Search Engine',3,3,0,0,0),(266,'Search Engine',4,3,0,0,0),(267,'Search Engine',13,3,0,0,0),(268,'Advertising Agencies',9,3,0,0,0),(269,'Advertising Agencies',3,3,0,0,0),(270,'Advertising Agencies',4,3,0,0,0),(271,'Advertising Agencies',13,3,0,0,0),(272,'Content Providers',9,3,0,0,0),(273,'Content Providers',3,3,0,0,0),(274,'Content Providers',4,3,0,0,0),(275,'Content Providers',13,3,0,0,0),(276,'Photobrowsers',9,3,0,0,0),(277,'Photobrowsers',3,3,0,0,0),(278,'Photobrowsers',4,3,0,0,0),(279,'Photobrowsers',13,3,0,0,0),(280,'Telco Operators',9,3,0,0,0),(281,'Telco Operators',3,3,0,0,0),(282,'Telco Operators',4,3,0,0,0),(283,'Telco Operators',13,3,0,0,0),(284,'Infoproviders',9,3,0,0,0),(285,'Infoproviders',3,3,0,0,0),(286,'Infoproviders',4,3,0,0,0),(287,'Infoproviders',13,3,0,0,0),(288,'Delivery Infrastructure',9,3,0,0,0),(289,'Delivery Infrastructure',3,3,0,0,0),(290,'Delivery Infrastructure',4,3,0,0,0),(291,'Delivery Infrastructure',13,3,0,0,0),(292,'Television Service Providers',9,3,0,0,0),(293,'Television Service Providers',3,3,0,0,0),(294,'Television Service Providers',4,3,0,0,0),(295,'Television Service Providers',13,3,0,0,0),(296,'Internet Service Providers',9,3,0,0,0),(297,'Internet Service Providers',3,3,0,0,0),(298,'Internet Service Providers',4,3,0,0,0),(299,'Internet Service Providers',13,3,0,0,0),(300,'Bookstores',9,3,0,0,0),(301,'Bookstores',3,3,0,0,0),(302,'Bookstores',4,3,0,0,0),(303,'Bookstores',13,3,0,0,0),(304,'Bookstalls',9,3,0,0,0),(305,'Bookstalls',3,3,0,0,0),(306,'Bookstalls',4,3,0,0,0),(307,'Bookstalls',13,3,0,0,0),(308,'Cell Phone Producers',9,3,0,0,0),(309,'Cell Phone Producers',3,3,0,0,0),(310,'Cell Phone Producers',4,3,0,0,0),(311,'Cell Phone Producers',13,3,0,0,0),(312,'E Reader',9,3,0,0,0),(313,'E Reader',3,3,0,0,0),(314,'E Reader',4,3,0,0,0),(315,'E Reader',13,3,0,0,0),(316,'Social Bookmarking Engine',9,3,0,0,0),(317,'Social Bookmarking Engine',3,3,0,0,0),(318,'Social Bookmarking Engine',4,3,0,0,0),(319,'Social Bookmarking Engine',13,3,0,0,0),(320,'Qr Tags',9,3,0,0,0),(321,'Qr Tags',3,3,0,0,0),(322,'Qr Tags',4,3,0,0,0),(323,'Qr Tags',13,3,0,0,0),(324,'Rfid Tags',9,3,0,0,0),(325,'Rfid Tags',3,3,0,0,0),(326,'Rfid Tags',4,3,0,0,0),(327,'Rfid Tags',13,3,0,0,0),(328,'Ocr',9,3,0,0,0),(329,'Ocr',3,3,0,0,0),(330,'Ocr',4,3,0,0,0),(331,'Ocr',13,3,0,0,0),(332,'Rfid Readers Provider',9,3,0,0,0),(333,'Rfid Readers Provider',3,3,0,0,0),(334,'Rfid Readers Provider',4,3,0,0,0),(335,'Rfid Readers Provider',13,3,0,0,0),(336,'System Integrator',9,3,0,0,0),(337,'System Integrator',3,3,0,0,0),(338,'System Integrator',4,3,0,0,0),(339,'System Integrator',13,3,0,0,0),(340,'Regulatory Agency',9,3,0,0,0),(341,'Regulatory Agency',3,3,0,0,0),(342,'Regulatory Agency',4,3,0,0,0),(343,'Regulatory Agency',13,3,0,0,0),(344,'Rfid Producers',9,3,0,0,0),(345,'Rfid Producers',3,3,0,0,0),(346,'Rfid Producers',4,3,0,0,0),(347,'Rfid Producers',13,3,0,0,0),(348,'Standard Code Agencies',9,3,0,0,0),(349,'Standard Code Agencies',3,3,0,0,0),(350,'Standard Code Agencies',4,3,0,0,0),(351,'Standard Code Agencies',13,3,0,0,0);
/*!40000 ALTER TABLE `ieeetags_node` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ieeetags_node_filters`
--

DROP TABLE IF EXISTS `ieeetags_node_filters`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `ieeetags_node_filters` (
  `id` int(11) NOT NULL auto_increment,
  `node_id` int(11) NOT NULL,
  `filter_id` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `node_id` (`node_id`,`filter_id`),
  KEY `filter_id_refs_id_1340c915` (`filter_id`),
  CONSTRAINT `filter_id_refs_id_1340c915` FOREIGN KEY (`filter_id`) REFERENCES `ieeetags_filter` (`id`),
  CONSTRAINT `node_id_refs_id_2d5d995f` FOREIGN KEY (`node_id`) REFERENCES `ieeetags_node` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=757 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `ieeetags_node_filters`
--

LOCK TABLES `ieeetags_node_filters` WRITE;
/*!40000 ALTER TABLE `ieeetags_node_filters` DISABLE KEYS */;
INSERT INTO `ieeetags_node_filters` VALUES (1,1,1),(2,1,2),(3,1,3),(4,1,4),(5,2,1),(6,2,2),(7,2,3),(8,2,4),(9,3,1),(10,3,2),(11,3,3),(12,3,4),(13,4,1),(14,4,2),(15,4,3),(16,4,4),(17,5,1),(18,5,2),(19,5,3),(20,5,4),(21,6,1),(22,6,2),(23,6,3),(24,6,4),(25,7,1),(26,7,2),(27,7,3),(28,7,4),(29,8,1),(30,8,2),(31,8,3),(32,8,4),(33,9,1),(34,9,2),(35,9,3),(36,9,4),(37,10,1),(38,10,2),(39,10,3),(40,10,4),(41,11,1),(42,11,2),(43,11,3),(44,11,4),(45,12,1),(46,12,2),(47,12,3),(48,12,4),(49,13,1),(50,13,2),(51,13,3),(52,13,4),(53,14,1),(54,14,2),(55,14,3),(56,14,4),(57,15,1),(58,15,2),(59,15,3),(60,15,4),(525,240,5),(526,240,6),(527,241,5),(528,241,6),(529,242,5),(530,242,6),(531,243,5),(532,243,6),(533,244,5),(534,244,6),(535,245,5),(536,245,6),(537,246,5),(538,246,6),(539,247,5),(540,247,6),(541,248,5),(542,248,6),(543,249,5),(544,249,6),(545,250,5),(546,250,6),(547,251,5),(548,251,6),(549,252,5),(550,252,6),(551,253,5),(552,253,6),(553,254,5),(554,254,6),(555,255,5),(556,255,6),(557,256,5),(558,256,6),(559,257,5),(560,257,6),(561,258,5),(562,258,6),(563,259,5),(564,259,6),(565,260,5),(566,260,6),(567,261,5),(568,261,6),(569,262,5),(570,262,6),(571,263,5),(572,263,6),(573,264,5),(574,264,6),(575,265,5),(576,265,6),(577,266,5),(578,266,6),(579,267,5),(580,267,6),(581,268,5),(582,268,6),(583,269,5),(584,269,6),(585,270,5),(586,270,6),(587,271,5),(588,271,6),(589,272,5),(590,272,6),(591,273,5),(592,273,6),(593,274,5),(594,274,6),(595,275,5),(596,275,6),(597,280,5),(598,280,6),(599,281,5),(600,281,6),(601,282,5),(602,282,6),(603,283,5),(604,283,6),(605,284,5),(606,284,6),(607,285,5),(608,285,6),(609,286,5),(610,286,6),(611,287,5),(612,287,6),(613,288,5),(614,288,6),(615,289,5),(616,289,6),(617,290,5),(618,290,6),(619,291,5),(620,291,6),(621,292,5),(622,292,6),(623,293,5),(624,293,6),(625,294,5),(626,294,6),(627,295,5),(628,295,6),(629,296,5),(630,296,6),(631,297,5),(632,297,6),(633,298,5),(634,298,6),(635,299,5),(636,299,6),(637,300,5),(638,300,6),(639,301,5),(640,301,6),(641,302,5),(642,302,6),(643,303,5),(644,303,6),(645,304,5),(646,304,6),(647,305,5),(648,305,6),(649,306,5),(650,306,6),(651,307,5),(652,307,6),(653,308,5),(654,308,6),(655,309,5),(656,309,6),(657,310,5),(658,310,6),(659,311,5),(660,311,6),(661,312,1),(662,312,5),(663,312,7),(664,313,1),(665,313,5),(666,313,7),(667,314,1),(668,314,5),(669,314,7),(670,315,1),(671,315,5),(672,315,7),(673,316,5),(674,316,6),(675,317,5),(676,317,6),(677,318,5),(678,318,6),(679,319,5),(680,319,6),(681,320,1),(682,320,5),(683,320,7),(684,321,1),(685,321,5),(686,321,7),(687,322,1),(688,322,5),(689,322,7),(690,323,1),(691,323,5),(692,323,7),(693,324,1),(694,324,5),(695,324,7),(696,325,1),(697,325,5),(698,325,7),(699,326,1),(700,326,5),(701,326,7),(702,327,1),(703,327,5),(704,327,7),(705,328,1),(706,328,5),(707,328,7),(708,329,1),(709,329,5),(710,329,7),(711,330,1),(712,330,5),(713,330,7),(714,331,1),(715,331,5),(716,331,7),(717,332,5),(718,332,6),(719,333,5),(720,333,6),(721,334,5),(722,334,6),(723,335,5),(724,335,6),(725,336,5),(726,336,6),(727,337,5),(728,337,6),(729,338,5),(730,338,6),(731,339,5),(732,339,6),(733,340,5),(734,340,6),(735,341,5),(736,341,6),(737,342,5),(738,342,6),(739,343,5),(740,343,6),(741,344,5),(742,344,6),(743,345,5),(744,345,6),(745,346,5),(746,346,6),(747,347,5),(748,347,6),(749,348,5),(750,348,6),(751,349,5),(752,349,6),(753,350,5),(754,350,6),(755,351,5),(756,351,6);
/*!40000 ALTER TABLE `ieeetags_node_filters` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ieeetags_node_related_sectors`
--

DROP TABLE IF EXISTS `ieeetags_node_related_sectors`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `ieeetags_node_related_sectors` (
  `id` int(11) NOT NULL auto_increment,
  `from_node_id` int(11) NOT NULL,
  `to_node_id` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `from_node_id` (`from_node_id`,`to_node_id`),
  KEY `to_node_id_refs_id_747bba37` (`to_node_id`),
  CONSTRAINT `to_node_id_refs_id_747bba37` FOREIGN KEY (`to_node_id`) REFERENCES `ieeetags_node` (`id`),
  CONSTRAINT `from_node_id_refs_id_747bba37` FOREIGN KEY (`from_node_id`) REFERENCES `ieeetags_node` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `ieeetags_node_related_sectors`
--

LOCK TABLES `ieeetags_node_related_sectors` WRITE;
/*!40000 ALTER TABLE `ieeetags_node_related_sectors` DISABLE KEYS */;
/*!40000 ALTER TABLE `ieeetags_node_related_sectors` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ieeetags_node_related_tags`
--

DROP TABLE IF EXISTS `ieeetags_node_related_tags`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `ieeetags_node_related_tags` (
  `id` int(11) NOT NULL auto_increment,
  `from_node_id` int(11) NOT NULL,
  `to_node_id` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `from_node_id` (`from_node_id`,`to_node_id`),
  KEY `to_node_id_refs_id_3cec9c56` (`to_node_id`),
  CONSTRAINT `to_node_id_refs_id_3cec9c56` FOREIGN KEY (`to_node_id`) REFERENCES `ieeetags_node` (`id`),
  CONSTRAINT `from_node_id_refs_id_3cec9c56` FOREIGN KEY (`from_node_id`) REFERENCES `ieeetags_node` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5209 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `ieeetags_node_related_tags`
--

LOCK TABLES `ieeetags_node_related_tags` WRITE;
/*!40000 ALTER TABLE `ieeetags_node_related_tags` DISABLE KEYS */;
INSERT INTO `ieeetags_node_related_tags` VALUES (3401,240,268),(3433,240,269),(3465,240,270),(3497,240,271),(3403,241,268),(3435,241,269),(3467,241,270),(3499,241,271),(3408,242,268),(3440,242,269),(3472,242,270),(3504,242,271),(3402,243,268),(3434,243,269),(3466,243,270),(3498,243,271),(3413,244,268),(3445,244,269),(3477,244,270),(3509,244,271),(3831,244,320),(3871,244,321),(3911,244,322),(3951,244,323),(3414,245,268),(3446,245,269),(3478,245,270),(3510,245,271),(3840,245,320),(3880,245,321),(3920,245,322),(3960,245,323),(3415,246,268),(3447,246,269),(3479,246,270),(3511,246,271),(3833,246,320),(3873,246,321),(3913,246,322),(3953,246,323),(3416,247,268),(3448,247,269),(3480,247,270),(3512,247,271),(3834,247,320),(3874,247,321),(3914,247,322),(3954,247,323),(3404,264,268),(3436,264,269),(3468,264,270),(3500,264,271),(3745,264,316),(3761,264,317),(3777,264,318),(3793,264,319),(3405,265,268),(3437,265,269),(3469,265,270),(3501,265,271),(3746,265,316),(3762,265,317),(3778,265,318),(3794,265,319),(3406,266,268),(3438,266,269),(3470,266,270),(3502,266,271),(3747,266,316),(3763,266,317),(3779,266,318),(3795,266,319),(3407,267,268),(3439,267,269),(3471,267,270),(3503,267,271),(3748,267,316),(3764,267,317),(3780,267,318),(3796,267,319),(3385,268,240),(3387,268,241),(3392,268,242),(3386,268,243),(3397,268,244),(3398,268,245),(3399,268,246),(3400,268,247),(3388,268,264),(3389,268,265),(3390,268,266),(3391,268,267),(3517,268,272),(3525,268,273),(3533,268,274),(3541,268,275),(3749,268,316),(3765,268,317),(3781,268,318),(3797,268,319),(3417,269,240),(3419,269,241),(3424,269,242),(3418,269,243),(3429,269,244),(3430,269,245),(3431,269,246),(3432,269,247),(3420,269,264),(3421,269,265),(3422,269,266),(3423,269,267),(3518,269,272),(3526,269,273),(3534,269,274),(3542,269,275),(3750,269,316),(3766,269,317),(3782,269,318),(3798,269,319),(3449,270,240),(3451,270,241),(3456,270,242),(3450,270,243),(3461,270,244),(3462,270,245),(3463,270,246),(3464,270,247),(3452,270,264),(3453,270,265),(3454,270,266),(3455,270,267),(3519,270,272),(3527,270,273),(3535,270,274),(3543,270,275),(3751,270,316),(3767,270,317),(3783,270,318),(3799,270,319),(3481,271,240),(3483,271,241),(3488,271,242),(3482,271,243),(3493,271,244),(3494,271,245),(3495,271,246),(3496,271,247),(3484,271,264),(3485,271,265),(3486,271,266),(3487,271,267),(3520,271,272),(3528,271,273),(3536,271,274),(3544,271,275),(3752,271,316),(3768,271,317),(3784,271,318),(3800,271,319),(3513,272,268),(3514,272,269),(3515,272,270),(3516,272,271),(3521,273,268),(3522,273,269),(3523,273,270),(3524,273,271),(3529,274,268),(3530,274,269),(3531,274,270),(3532,274,271),(3537,275,268),(3538,275,269),(3539,275,270),(3540,275,271),(3677,280,308),(3685,280,309),(3693,280,310),(3701,280,311),(4245,280,332),(4301,280,333),(4357,280,334),(4413,280,335),(4477,280,336),(4549,280,337),(4621,280,338),(4693,280,339),(4765,280,340),(4837,280,341),(4909,280,342),(4981,280,343),(3678,281,308),(3686,281,309),(3694,281,310),(3702,281,311),(4246,281,332),(4302,281,333),(4358,281,334),(4414,281,335),(4478,281,336),(4550,281,337),(4622,281,338),(4694,281,339),(4766,281,340),(4838,281,341),(4910,281,342),(4982,281,343),(3679,282,308),(3687,282,309),(3695,282,310),(3703,282,311),(4247,282,332),(4303,282,333),(4359,282,334),(4415,282,335),(4479,282,336),(4551,282,337),(4623,282,338),(4695,282,339),(4767,282,340),(4839,282,341),(4911,282,342),(4983,282,343),(3680,283,308),(3688,283,309),(3696,283,310),(3704,283,311),(4248,283,332),(4304,283,333),(4360,283,334),(4416,283,335),(4480,283,336),(4552,283,337),(4624,283,338),(4696,283,339),(4768,283,340),(4840,283,341),(4912,283,342),(4984,283,343),(3621,284,296),(3637,284,297),(3653,284,298),(3669,284,299),(3622,285,296),(3638,285,297),(3654,285,298),(3670,285,299),(3623,286,296),(3639,286,297),(3655,286,298),(3671,286,299),(3624,287,296),(3640,287,297),(3656,287,298),(3672,287,299),(3613,296,284),(3614,296,285),(3615,296,286),(3616,296,287),(3709,296,312),(3717,296,313),(3725,296,314),(3733,296,315),(3629,297,284),(3630,297,285),(3631,297,286),(3632,297,287),(3710,297,312),(3718,297,313),(3726,297,314),(3734,297,315),(3645,298,284),(3646,298,285),(3647,298,286),(3648,298,287),(3711,298,312),(3719,298,313),(3727,298,314),(3735,298,315),(3661,299,284),(3662,299,285),(3663,299,286),(3664,299,287),(3712,299,312),(3720,299,313),(3728,299,314),(3736,299,315),(3673,308,280),(3674,308,281),(3675,308,282),(3676,308,283),(4249,308,332),(4305,308,333),(4361,308,334),(4417,308,335),(4481,308,336),(4553,308,337),(4625,308,338),(4697,308,339),(4769,308,340),(4841,308,341),(4913,308,342),(4985,308,343),(3681,309,280),(3682,309,281),(3683,309,282),(3684,309,283),(4250,309,332),(4306,309,333),(4362,309,334),(4418,309,335),(4482,309,336),(4554,309,337),(4626,309,338),(4698,309,339),(4770,309,340),(4842,309,341),(4914,309,342),(4986,309,343),(3689,310,280),(3690,310,281),(3691,310,282),(3692,310,283),(4251,310,332),(4307,310,333),(4363,310,334),(4419,310,335),(4483,310,336),(4555,310,337),(4627,310,338),(4699,310,339),(4771,310,340),(4843,310,341),(4915,310,342),(4987,310,343),(3697,311,280),(3698,311,281),(3699,311,282),(3700,311,283),(4252,311,332),(4308,311,333),(4364,311,334),(4420,311,335),(4484,311,336),(4556,311,337),(4628,311,338),(4700,311,339),(4772,311,340),(4844,311,341),(4916,311,342),(4988,311,343),(3705,312,296),(3706,312,297),(3707,312,298),(3708,312,299),(3835,312,320),(3875,312,321),(3915,312,322),(3955,312,323),(3985,312,324),(4033,312,325),(4081,312,326),(4129,312,327),(4253,312,332),(4309,312,333),(4365,312,334),(4421,312,335),(4485,312,336),(4557,312,337),(4629,312,338),(4701,312,339),(4773,312,340),(4845,312,341),(4917,312,342),(4989,312,343),(3713,313,296),(3714,313,297),(3715,313,298),(3716,313,299),(3839,313,320),(3879,313,321),(3919,313,322),(3959,313,323),(3986,313,324),(4034,313,325),(4082,313,326),(4130,313,327),(4254,313,332),(4310,313,333),(4366,313,334),(4422,313,335),(4486,313,336),(4558,313,337),(4630,313,338),(4702,313,339),(4774,313,340),(4846,313,341),(4918,313,342),(4990,313,343),(3721,314,296),(3722,314,297),(3723,314,298),(3724,314,299),(3837,314,320),(3877,314,321),(3917,314,322),(3957,314,323),(3987,314,324),(4035,314,325),(4083,314,326),(4131,314,327),(4255,314,332),(4311,314,333),(4367,314,334),(4423,314,335),(4487,314,336),(4559,314,337),(4631,314,338),(4703,314,339),(4775,314,340),(4847,314,341),(4919,314,342),(4991,314,343),(3729,315,296),(3730,315,297),(3731,315,298),(3732,315,299),(3838,315,320),(3878,315,321),(3918,315,322),(3958,315,323),(3988,315,324),(4036,315,325),(4084,315,326),(4132,315,327),(4256,315,332),(4312,315,333),(4368,315,334),(4424,315,335),(4488,315,336),(4560,315,337),(4632,315,338),(4704,315,339),(4776,315,340),(4848,315,341),(4920,315,342),(4992,315,343),(3737,316,264),(3738,316,265),(3739,316,266),(3740,316,267),(3741,316,268),(3742,316,269),(3743,316,270),(3744,316,271),(3753,317,264),(3754,317,265),(3755,317,266),(3756,317,267),(3757,317,268),(3758,317,269),(3759,317,270),(3760,317,271),(3769,318,264),(3770,318,265),(3771,318,266),(3772,318,267),(3773,318,268),(3774,318,269),(3775,318,270),(3776,318,271),(3785,319,264),(3786,319,265),(3787,319,266),(3788,319,267),(3789,319,268),(3790,319,269),(3791,319,270),(3792,319,271),(3811,320,244),(3820,320,245),(3813,320,246),(3814,320,247),(3815,320,312),(3819,320,313),(3817,320,314),(3818,320,315),(4257,320,332),(4313,320,333),(4369,320,334),(4425,320,335),(4489,320,336),(4561,320,337),(4633,320,338),(4705,320,339),(4777,320,340),(4849,320,341),(4921,320,342),(4993,320,343),(3851,321,244),(3860,321,245),(3853,321,246),(3854,321,247),(3855,321,312),(3859,321,313),(3857,321,314),(3858,321,315),(4258,321,332),(4314,321,333),(4370,321,334),(4426,321,335),(4490,321,336),(4562,321,337),(4634,321,338),(4706,321,339),(4778,321,340),(4850,321,341),(4922,321,342),(4994,321,343),(3891,322,244),(3900,322,245),(3893,322,246),(3894,322,247),(3895,322,312),(3899,322,313),(3897,322,314),(3898,322,315),(4259,322,332),(4315,322,333),(4371,322,334),(4427,322,335),(4491,322,336),(4563,322,337),(4635,322,338),(4707,322,339),(4779,322,340),(4851,322,341),(4923,322,342),(4995,322,343),(3931,323,244),(3940,323,245),(3933,323,246),(3934,323,247),(3935,323,312),(3939,323,313),(3937,323,314),(3938,323,315),(4260,323,332),(4316,323,333),(4372,323,334),(4428,323,335),(4492,323,336),(4564,323,337),(4636,323,338),(4708,323,339),(4780,323,340),(4852,323,341),(4924,323,342),(4996,323,343),(3961,324,312),(3962,324,313),(3963,324,314),(3964,324,315),(4261,324,332),(4317,324,333),(4373,324,334),(4429,324,335),(4493,324,336),(4565,324,337),(4637,324,338),(4709,324,339),(4781,324,340),(4853,324,341),(4925,324,342),(4997,324,343),(5033,324,344),(5065,324,345),(5097,324,346),(5129,324,347),(5153,324,348),(5169,324,349),(5185,324,350),(5201,324,351),(4009,325,312),(4010,325,313),(4011,325,314),(4012,325,315),(4262,325,332),(4318,325,333),(4374,325,334),(4430,325,335),(4494,325,336),(4566,325,337),(4638,325,338),(4710,325,339),(4782,325,340),(4854,325,341),(4926,325,342),(4998,325,343),(5034,325,344),(5066,325,345),(5098,325,346),(5130,325,347),(5154,325,348),(5170,325,349),(5186,325,350),(5202,325,351),(4057,326,312),(4058,326,313),(4059,326,314),(4060,326,315),(4263,326,332),(4319,326,333),(4375,326,334),(4431,326,335),(4495,326,336),(4567,326,337),(4639,326,338),(4711,326,339),(4783,326,340),(4855,326,341),(4927,326,342),(4999,326,343),(5035,326,344),(5067,326,345),(5099,326,346),(5131,326,347),(5155,326,348),(5171,326,349),(5187,326,350),(5203,326,351),(4105,327,312),(4106,327,313),(4107,327,314),(4108,327,315),(4264,327,332),(4320,327,333),(4376,327,334),(4432,327,335),(4496,327,336),(4568,327,337),(4640,327,338),(4712,327,339),(4784,327,340),(4856,327,341),(4928,327,342),(5000,327,343),(5036,327,344),(5068,327,345),(5100,327,346),(5132,327,347),(5156,327,348),(5172,327,349),(5188,327,350),(5204,327,351),(4265,328,332),(4321,328,333),(4377,328,334),(4433,328,335),(4497,328,336),(4569,328,337),(4641,328,338),(4713,328,339),(4785,328,340),(4857,328,341),(4929,328,342),(5001,328,343),(4266,329,332),(4322,329,333),(4378,329,334),(4434,329,335),(4498,329,336),(4570,329,337),(4642,329,338),(4714,329,339),(4786,329,340),(4858,329,341),(4930,329,342),(5002,329,343),(4267,330,332),(4323,330,333),(4379,330,334),(4435,330,335),(4499,330,336),(4571,330,337),(4643,330,338),(4715,330,339),(4787,330,340),(4859,330,341),(4931,330,342),(5003,330,343),(4268,331,332),(4324,331,333),(4380,331,334),(4436,331,335),(4500,331,336),(4572,331,337),(4644,331,338),(4716,331,339),(4788,331,340),(4860,331,341),(4932,331,342),(5004,331,343),(4217,332,280),(4218,332,281),(4219,332,282),(4220,332,283),(4221,332,308),(4222,332,309),(4223,332,310),(4224,332,311),(4225,332,312),(4226,332,313),(4227,332,314),(4228,332,315),(4229,332,320),(4230,332,321),(4231,332,322),(4232,332,323),(4233,332,324),(4234,332,325),(4235,332,326),(4236,332,327),(4237,332,328),(4238,332,329),(4239,332,330),(4240,332,331),(5037,332,344),(5069,332,345),(5101,332,346),(5133,332,347),(4273,333,280),(4274,333,281),(4275,333,282),(4276,333,283),(4277,333,308),(4278,333,309),(4279,333,310),(4280,333,311),(4281,333,312),(4282,333,313),(4283,333,314),(4284,333,315),(4285,333,320),(4286,333,321),(4287,333,322),(4288,333,323),(4289,333,324),(4290,333,325),(4291,333,326),(4292,333,327),(4293,333,328),(4294,333,329),(4295,333,330),(4296,333,331),(5038,333,344),(5070,333,345),(5102,333,346),(5134,333,347),(4329,334,280),(4330,334,281),(4331,334,282),(4332,334,283),(4333,334,308),(4334,334,309),(4335,334,310),(4336,334,311),(4337,334,312),(4338,334,313),(4339,334,314),(4340,334,315),(4341,334,320),(4342,334,321),(4343,334,322),(4344,334,323),(4345,334,324),(4346,334,325),(4347,334,326),(4348,334,327),(4349,334,328),(4350,334,329),(4351,334,330),(4352,334,331),(5039,334,344),(5071,334,345),(5103,334,346),(5135,334,347),(4385,335,280),(4386,335,281),(4387,335,282),(4388,335,283),(4389,335,308),(4390,335,309),(4391,335,310),(4392,335,311),(4393,335,312),(4394,335,313),(4395,335,314),(4396,335,315),(4397,335,320),(4398,335,321),(4399,335,322),(4400,335,323),(4401,335,324),(4402,335,325),(4403,335,326),(4404,335,327),(4405,335,328),(4406,335,329),(4407,335,330),(4408,335,331),(5040,335,344),(5072,335,345),(5104,335,346),(5136,335,347),(4441,336,280),(4442,336,281),(4443,336,282),(4444,336,283),(4445,336,308),(4446,336,309),(4447,336,310),(4448,336,311),(4449,336,312),(4450,336,313),(4451,336,314),(4452,336,315),(4453,336,320),(4454,336,321),(4455,336,322),(4456,336,323),(4457,336,324),(4458,336,325),(4459,336,326),(4460,336,327),(4461,336,328),(4462,336,329),(4463,336,330),(4464,336,331),(4789,336,340),(4861,336,341),(4933,336,342),(5005,336,343),(5041,336,344),(5073,336,345),(5105,336,346),(5137,336,347),(4513,337,280),(4514,337,281),(4515,337,282),(4516,337,283),(4517,337,308),(4518,337,309),(4519,337,310),(4520,337,311),(4521,337,312),(4522,337,313),(4523,337,314),(4524,337,315),(4525,337,320),(4526,337,321),(4527,337,322),(4528,337,323),(4529,337,324),(4530,337,325),(4531,337,326),(4532,337,327),(4533,337,328),(4534,337,329),(4535,337,330),(4536,337,331),(4790,337,340),(4862,337,341),(4934,337,342),(5006,337,343),(5042,337,344),(5074,337,345),(5106,337,346),(5138,337,347),(4585,338,280),(4586,338,281),(4587,338,282),(4588,338,283),(4589,338,308),(4590,338,309),(4591,338,310),(4592,338,311),(4593,338,312),(4594,338,313),(4595,338,314),(4596,338,315),(4597,338,320),(4598,338,321),(4599,338,322),(4600,338,323),(4601,338,324),(4602,338,325),(4603,338,326),(4604,338,327),(4605,338,328),(4606,338,329),(4607,338,330),(4608,338,331),(4791,338,340),(4863,338,341),(4935,338,342),(5007,338,343),(5043,338,344),(5075,338,345),(5107,338,346),(5139,338,347),(4657,339,280),(4658,339,281),(4659,339,282),(4660,339,283),(4661,339,308),(4662,339,309),(4663,339,310),(4664,339,311),(4665,339,312),(4666,339,313),(4667,339,314),(4668,339,315),(4669,339,320),(4670,339,321),(4671,339,322),(4672,339,323),(4673,339,324),(4674,339,325),(4675,339,326),(4676,339,327),(4677,339,328),(4678,339,329),(4679,339,330),(4680,339,331),(4792,339,340),(4864,339,341),(4936,339,342),(5008,339,343),(5044,339,344),(5076,339,345),(5108,339,346),(5140,339,347),(4729,340,280),(4730,340,281),(4731,340,282),(4732,340,283),(4733,340,308),(4734,340,309),(4735,340,310),(4736,340,311),(4737,340,312),(4738,340,313),(4739,340,314),(4740,340,315),(4741,340,320),(4742,340,321),(4743,340,322),(4744,340,323),(4745,340,324),(4746,340,325),(4747,340,326),(4748,340,327),(4749,340,328),(4750,340,329),(4751,340,330),(4752,340,331),(4753,340,336),(4754,340,337),(4755,340,338),(4756,340,339),(4801,341,280),(4802,341,281),(4803,341,282),(4804,341,283),(4805,341,308),(4806,341,309),(4807,341,310),(4808,341,311),(4809,341,312),(4810,341,313),(4811,341,314),(4812,341,315),(4813,341,320),(4814,341,321),(4815,341,322),(4816,341,323),(4817,341,324),(4818,341,325),(4819,341,326),(4820,341,327),(4821,341,328),(4822,341,329),(4823,341,330),(4824,341,331),(4825,341,336),(4826,341,337),(4827,341,338),(4828,341,339),(4873,342,280),(4874,342,281),(4875,342,282),(4876,342,283),(4877,342,308),(4878,342,309),(4879,342,310),(4880,342,311),(4881,342,312),(4882,342,313),(4883,342,314),(4884,342,315),(4885,342,320),(4886,342,321),(4887,342,322),(4888,342,323),(4889,342,324),(4890,342,325),(4891,342,326),(4892,342,327),(4893,342,328),(4894,342,329),(4895,342,330),(4896,342,331),(4897,342,336),(4898,342,337),(4899,342,338),(4900,342,339),(4945,343,280),(4946,343,281),(4947,343,282),(4948,343,283),(4949,343,308),(4950,343,309),(4951,343,310),(4952,343,311),(4953,343,312),(4954,343,313),(4955,343,314),(4956,343,315),(4957,343,320),(4958,343,321),(4959,343,322),(4960,343,323),(4961,343,324),(4962,343,325),(4963,343,326),(4964,343,327),(4965,343,328),(4966,343,329),(4967,343,330),(4968,343,331),(4969,343,336),(4970,343,337),(4971,343,338),(4972,343,339),(5017,344,324),(5018,344,325),(5019,344,326),(5020,344,327),(5021,344,332),(5022,344,333),(5023,344,334),(5024,344,335),(5025,344,336),(5026,344,337),(5027,344,338),(5028,344,339),(5157,344,348),(5173,344,349),(5189,344,350),(5205,344,351),(5049,345,324),(5050,345,325),(5051,345,326),(5052,345,327),(5053,345,332),(5054,345,333),(5055,345,334),(5056,345,335),(5057,345,336),(5058,345,337),(5059,345,338),(5060,345,339),(5158,345,348),(5174,345,349),(5190,345,350),(5206,345,351),(5081,346,324),(5082,346,325),(5083,346,326),(5084,346,327),(5085,346,332),(5086,346,333),(5087,346,334),(5088,346,335),(5089,346,336),(5090,346,337),(5091,346,338),(5092,346,339),(5159,346,348),(5175,346,349),(5191,346,350),(5207,346,351),(5113,347,324),(5114,347,325),(5115,347,326),(5116,347,327),(5117,347,332),(5118,347,333),(5119,347,334),(5120,347,335),(5121,347,336),(5122,347,337),(5123,347,338),(5124,347,339),(5160,347,348),(5176,347,349),(5192,347,350),(5208,347,351),(5145,348,324),(5146,348,325),(5147,348,326),(5148,348,327),(5149,348,344),(5150,348,345),(5151,348,346),(5152,348,347),(5161,349,324),(5162,349,325),(5163,349,326),(5164,349,327),(5165,349,344),(5166,349,345),(5167,349,346),(5168,349,347),(5177,350,324),(5178,350,325),(5179,350,326),(5180,350,327),(5181,350,344),(5182,350,345),(5183,350,346),(5184,350,347),(5193,351,324),(5194,351,325),(5195,351,326),(5196,351,327),(5197,351,344),(5198,351,345),(5199,351,346),(5200,351,347);
/*!40000 ALTER TABLE `ieeetags_node_related_tags` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ieeetags_node_societies`
--

DROP TABLE IF EXISTS `ieeetags_node_societies`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `ieeetags_node_societies` (
  `id` int(11) NOT NULL auto_increment,
  `node_id` int(11) NOT NULL,
  `society_id` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `node_id` (`node_id`,`society_id`),
  KEY `society_id_refs_id_4283f3d1` (`society_id`),
  CONSTRAINT `society_id_refs_id_4283f3d1` FOREIGN KEY (`society_id`) REFERENCES `ieeetags_society` (`id`),
  CONSTRAINT `node_id_refs_id_151b8f74` FOREIGN KEY (`node_id`) REFERENCES `ieeetags_node` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=225 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `ieeetags_node_societies`
--

LOCK TABLES `ieeetags_node_societies` WRITE;
/*!40000 ALTER TABLE `ieeetags_node_societies` DISABLE KEYS */;
INSERT INTO `ieeetags_node_societies` VALUES (113,240,1),(114,241,1),(115,242,1),(116,243,1),(117,244,1),(118,245,1),(119,246,1),(120,247,1),(121,248,1),(122,249,1),(123,250,1),(124,251,1),(125,252,1),(126,253,1),(127,254,1),(128,255,1),(129,256,1),(130,257,1),(131,258,1),(132,259,1),(133,260,1),(134,261,1),(135,262,1),(136,263,1),(137,264,1),(138,265,1),(139,266,1),(140,267,1),(141,268,1),(142,269,1),(143,270,1),(144,271,1),(145,272,1),(146,273,1),(147,274,1),(148,275,1),(149,276,1),(150,277,1),(151,278,1),(152,279,1),(153,280,1),(154,281,1),(155,282,1),(156,283,1),(157,284,1),(158,285,1),(159,286,1),(160,287,1),(161,288,1),(162,289,1),(163,290,1),(164,291,1),(165,292,1),(166,293,1),(167,294,1),(168,295,1),(169,296,1),(170,297,1),(171,298,1),(172,299,1),(173,300,1),(174,301,1),(175,302,1),(176,303,1),(177,304,1),(178,305,1),(179,306,1),(180,307,1),(181,308,1),(182,309,1),(183,310,1),(184,311,1),(185,312,1),(186,313,1),(187,314,1),(188,315,1),(189,316,1),(190,317,1),(191,318,1),(192,319,1),(193,320,1),(194,321,1),(195,322,1),(196,323,1),(197,324,1),(198,325,1),(199,326,1),(200,327,1),(201,328,1),(202,329,1),(203,330,1),(204,331,1),(205,332,1),(206,333,1),(207,334,1),(208,335,1),(209,336,1),(210,337,1),(211,338,1),(212,339,1),(213,340,1),(214,341,1),(215,342,1),(216,343,1),(217,344,1),(218,345,1),(219,346,1),(220,347,1),(221,348,1),(222,349,1),(223,350,1),(224,351,1);
/*!40000 ALTER TABLE `ieeetags_node_societies` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ieeetags_nodetype`
--

DROP TABLE IF EXISTS `ieeetags_nodetype`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `ieeetags_nodetype` (
  `id` int(11) NOT NULL auto_increment,
  `name` varchar(50) collate utf8_unicode_ci NOT NULL,
  PRIMARY KEY  (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `ieeetags_nodetype`
--

LOCK TABLES `ieeetags_nodetype` WRITE;
/*!40000 ALTER TABLE `ieeetags_nodetype` DISABLE KEYS */;
INSERT INTO `ieeetags_nodetype` VALUES (1,'root'),(2,'sector'),(3,'tag'),(4,'tag_cluster');
/*!40000 ALTER TABLE `ieeetags_nodetype` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ieeetags_permission`
--

DROP TABLE IF EXISTS `ieeetags_permission`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `ieeetags_permission` (
  `id` int(11) NOT NULL auto_increment,
  `user_id` int(11) NOT NULL,
  `object_type_id` int(11) NOT NULL,
  `object_id` int(10) unsigned NOT NULL,
  `permission_type` varchar(1000) collate utf8_unicode_ci NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `ieeetags_permission_user_id` (`user_id`),
  KEY `ieeetags_permission_object_type_id` (`object_type_id`),
  CONSTRAINT `object_type_id_refs_id_618b7840` FOREIGN KEY (`object_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `user_id_refs_id_51c9aa44` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `ieeetags_permission`
--

LOCK TABLES `ieeetags_permission` WRITE;
/*!40000 ALTER TABLE `ieeetags_permission` DISABLE KEYS */;
/*!40000 ALTER TABLE `ieeetags_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ieeetags_profile`
--

DROP TABLE IF EXISTS `ieeetags_profile`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `ieeetags_profile` (
  `id` int(11) NOT NULL auto_increment,
  `user_id` int(11) NOT NULL,
  `role` varchar(1000) collate utf8_unicode_ci NOT NULL,
  `reset_key` varchar(1000) collate utf8_unicode_ci default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `user_id_refs_id_5285cb49` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `ieeetags_profile`
--

LOCK TABLES `ieeetags_profile` WRITE;
/*!40000 ALTER TABLE `ieeetags_profile` DISABLE KEYS */;
INSERT INTO `ieeetags_profile` VALUES (1,1,'admin',NULL),(2,2,'society_manager',NULL),(3,3,'society_manager',NULL);
/*!40000 ALTER TABLE `ieeetags_profile` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ieeetags_resource`
--

DROP TABLE IF EXISTS `ieeetags_resource`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `ieeetags_resource` (
  `id` int(11) NOT NULL auto_increment,
  `resource_type_id` int(11) NOT NULL,
  `ieee_id` varchar(500) collate utf8_unicode_ci default NULL,
  `name` varchar(500) collate utf8_unicode_ci NOT NULL,
  `description` varchar(1000) collate utf8_unicode_ci NOT NULL,
  `url` varchar(1000) collate utf8_unicode_ci NOT NULL,
  `year` int(11) default NULL,
  `standard_status` varchar(100) collate utf8_unicode_ci NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `ieeetags_resource_resource_type_id` (`resource_type_id`),
  CONSTRAINT `resource_type_id_refs_id_21a19251` FOREIGN KEY (`resource_type_id`) REFERENCES `ieeetags_resourcetype` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `ieeetags_resource`
--

LOCK TABLES `ieeetags_resource` WRITE;
/*!40000 ALTER TABLE `ieeetags_resource` DISABLE KEYS */;
/*!40000 ALTER TABLE `ieeetags_resource` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ieeetags_resource_nodes`
--

DROP TABLE IF EXISTS `ieeetags_resource_nodes`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `ieeetags_resource_nodes` (
  `id` int(11) NOT NULL auto_increment,
  `resource_id` int(11) NOT NULL,
  `node_id` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `resource_id` (`resource_id`,`node_id`),
  KEY `node_id_refs_id_4d52045f` (`node_id`),
  CONSTRAINT `node_id_refs_id_4d52045f` FOREIGN KEY (`node_id`) REFERENCES `ieeetags_node` (`id`),
  CONSTRAINT `resource_id_refs_id_3c53589` FOREIGN KEY (`resource_id`) REFERENCES `ieeetags_resource` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `ieeetags_resource_nodes`
--

LOCK TABLES `ieeetags_resource_nodes` WRITE;
/*!40000 ALTER TABLE `ieeetags_resource_nodes` DISABLE KEYS */;
/*!40000 ALTER TABLE `ieeetags_resource_nodes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ieeetags_resource_societies`
--

DROP TABLE IF EXISTS `ieeetags_resource_societies`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `ieeetags_resource_societies` (
  `id` int(11) NOT NULL auto_increment,
  `resource_id` int(11) NOT NULL,
  `society_id` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `resource_id` (`resource_id`,`society_id`),
  KEY `society_id_refs_id_5593f5d1` (`society_id`),
  CONSTRAINT `society_id_refs_id_5593f5d1` FOREIGN KEY (`society_id`) REFERENCES `ieeetags_society` (`id`),
  CONSTRAINT `resource_id_refs_id_2e9a7be4` FOREIGN KEY (`resource_id`) REFERENCES `ieeetags_resource` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `ieeetags_resource_societies`
--

LOCK TABLES `ieeetags_resource_societies` WRITE;
/*!40000 ALTER TABLE `ieeetags_resource_societies` DISABLE KEYS */;
/*!40000 ALTER TABLE `ieeetags_resource_societies` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ieeetags_resourcetype`
--

DROP TABLE IF EXISTS `ieeetags_resourcetype`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `ieeetags_resourcetype` (
  `id` int(11) NOT NULL auto_increment,
  `name` varchar(50) collate utf8_unicode_ci NOT NULL,
  PRIMARY KEY  (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `ieeetags_resourcetype`
--

LOCK TABLES `ieeetags_resourcetype` WRITE;
/*!40000 ALTER TABLE `ieeetags_resourcetype` DISABLE KEYS */;
INSERT INTO `ieeetags_resourcetype` VALUES (1,'conference'),(2,'expert'),(3,'periodical'),(4,'standard');
/*!40000 ALTER TABLE `ieeetags_resourcetype` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ieeetags_society`
--

DROP TABLE IF EXISTS `ieeetags_society`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `ieeetags_society` (
  `id` int(11) NOT NULL auto_increment,
  `name` varchar(500) collate utf8_unicode_ci NOT NULL,
  `abbreviation` varchar(20) collate utf8_unicode_ci NOT NULL,
  `url` varchar(1000) collate utf8_unicode_ci NOT NULL,
  PRIMARY KEY  (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `ieeetags_society`
--

LOCK TABLES `ieeetags_society` WRITE;
/*!40000 ALTER TABLE `ieeetags_society` DISABLE KEYS */;
INSERT INTO `ieeetags_society` VALUES (1,'Communications','COM','http://');
/*!40000 ALTER TABLE `ieeetags_society` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ieeetags_society_users`
--

DROP TABLE IF EXISTS `ieeetags_society_users`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `ieeetags_society_users` (
  `id` int(11) NOT NULL auto_increment,
  `society_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `society_id` (`society_id`,`user_id`),
  KEY `user_id_refs_id_69d6ab23` (`user_id`),
  CONSTRAINT `user_id_refs_id_69d6ab23` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `society_id_refs_id_e1d6f1c` FOREIGN KEY (`society_id`) REFERENCES `ieeetags_society` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `ieeetags_society_users`
--

LOCK TABLES `ieeetags_society_users` WRITE;
/*!40000 ALTER TABLE `ieeetags_society_users` DISABLE KEYS */;
INSERT INTO `ieeetags_society_users` VALUES (1,1,2);
/*!40000 ALTER TABLE `ieeetags_society_users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2009-04-01 20:40:22
