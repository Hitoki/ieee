-- MySQL dump 10.11
--
-- Host: localhost    Database: ieeetags
-- ------------------------------------------------------
-- Server version	5.0.51b-community-nt

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
  `name` varchar(80) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
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
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
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
  `message` longtext NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `auth_message_user_id` (`user_id`),
  CONSTRAINT `user_id_refs_id_650f49a6` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
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
  `name` varchar(50) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `content_type_id` (`content_type_id`,`codename`),
  KEY `auth_permission_content_type_id` (`content_type_id`),
  CONSTRAINT `content_type_id_refs_id_728de91f` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=49 DEFAULT CHARSET=latin1;
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
  `username` varchar(30) NOT NULL,
  `first_name` varchar(30) NOT NULL,
  `last_name` varchar(30) NOT NULL,
  `email` varchar(75) NOT NULL,
  `password` varchar(128) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `last_login` datetime NOT NULL,
  `date_joined` datetime NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=latin1;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `auth_user`
--

LOCK TABLES `auth_user` WRITE;
/*!40000 ALTER TABLE `auth_user` DISABLE KEYS */;
INSERT INTO `auth_user` VALUES (1,'admin','Admin','','admin@systemicist.com','sha1$7524e$bb4a8fcc308e0e8a4451ce4428ecd7d487985fd5',1,1,1,'2009-03-17 15:36:21','2009-03-11 14:39:39'),(2,'soc','Society','','','sha1$314b1$ea2b7ef38fb49c42cc7ed529715aaeec99171a1a',1,1,0,'2009-03-11 14:41:06','2009-03-11 14:41:06'),(3,'multisoc','Society','(Multiple)','','sha1$5333e$0cf657779a783225185a94099d2086de360518a0',1,1,0,'2009-03-17 15:37:12','2009-03-17 15:37:12');
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
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
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
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
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
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint(5) unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `django_admin_log_user_id` (`user_id`),
  KEY `django_admin_log_content_type_id` (`content_type_id`),
  CONSTRAINT `content_type_id_refs_id_288599e6` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `user_id_refs_id_c8665aa` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
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
  `name` varchar(100) NOT NULL,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `app_label` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=latin1;
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
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime NOT NULL,
  PRIMARY KEY  (`session_key`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
INSERT INTO `django_session` VALUES ('45a740653fbb850c90c1ccbb747142f6','gAJ9cQEoVRJfYXV0aF91c2VyX2JhY2tlbmRxAlUpZGphbmdvLmNvbnRyaWIuYXV0aC5iYWNrZW5k\ncy5Nb2RlbEJhY2tlbmRxA1UNX2F1dGhfdXNlcl9pZHEEigEBdS5mMDhlNmU4NGJkMDgyOTEwN2Uz\nNmY2OGNiMDgxYzY5OQ==\n','2009-03-31 15:36:21');
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
  `domain` varchar(100) NOT NULL,
  `name` varchar(50) NOT NULL,
  PRIMARY KEY  (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;
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
  `name` varchar(50) NOT NULL,
  `value` varchar(500) NOT NULL,
  PRIMARY KEY  (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=latin1;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `ieeetags_filter`
--

LOCK TABLES `ieeetags_filter` WRITE;
/*!40000 ALTER TABLE `ieeetags_filter` DISABLE KEYS */;
INSERT INTO `ieeetags_filter` VALUES (1,'Emerging Technologies','emerging_technologies'),(2,'Foundation Technologies','foundation_technologies'),(3,'Hot Topics','hot_topics'),(4,'Market Areas','market_areas');
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
  `name` varchar(500) NOT NULL,
  `node_type_id` int(11) NOT NULL,
  `num_related_tags` int(11) default NULL,
  `num_resources` int(11) default NULL,
  PRIMARY KEY  (`id`),
  KEY `ieeetags_node_node_type_id` (`node_type_id`),
  CONSTRAINT `node_type_id_refs_id_652d089` FOREIGN KEY (`node_type_id`) REFERENCES `ieeetags_nodetype` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=latin1;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `ieeetags_node`
--

LOCK TABLES `ieeetags_node` WRITE;
/*!40000 ALTER TABLE `ieeetags_node` DISABLE KEYS */;
INSERT INTO `ieeetags_node` VALUES (1,'IEEE',1,NULL,NULL),(2,'Agriculture',2,NULL,NULL),(3,'Communications',2,NULL,NULL),(4,'Computing & IT',2,NULL,NULL),(5,'Critical Infrastructure',2,NULL,NULL),(6,'Defense',2,NULL,NULL),(7,'Education',2,NULL,NULL),(8,'Energy',2,NULL,NULL),(9,'Entertainment',2,NULL,NULL),(10,'Environment',2,NULL,NULL),(11,'Financial Services',2,NULL,NULL),(12,'Healthcare',2,NULL,NULL),(13,'Manufacturing & Devices',2,NULL,NULL),(14,'Retail',2,NULL,NULL),(15,'Transportation',2,NULL,NULL);
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
) ENGINE=InnoDB AUTO_INCREMENT=121 DEFAULT CHARSET=latin1;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `ieeetags_node_filters`
--

LOCK TABLES `ieeetags_node_filters` WRITE;
/*!40000 ALTER TABLE `ieeetags_node_filters` DISABLE KEYS */;
INSERT INTO `ieeetags_node_filters` VALUES (61,1,1),(62,1,2),(63,1,3),(64,1,4),(65,2,1),(66,2,2),(67,2,3),(68,2,4),(69,3,1),(70,3,2),(71,3,3),(72,3,4),(73,4,1),(74,4,2),(75,4,3),(76,4,4),(77,5,1),(78,5,2),(79,5,3),(80,5,4),(81,6,1),(82,6,2),(83,6,3),(84,6,4),(85,7,1),(86,7,2),(87,7,3),(88,7,4),(89,8,1),(90,8,2),(91,8,3),(92,8,4),(93,9,1),(94,9,2),(95,9,3),(96,9,4),(97,10,1),(98,10,2),(99,10,3),(100,10,4),(101,11,1),(102,11,2),(103,11,3),(104,11,4),(105,12,1),(106,12,2),(107,12,3),(108,12,4),(109,13,1),(110,13,2),(111,13,3),(112,13,4),(113,14,1),(114,14,2),(115,14,3),(116,14,4),(117,15,1),(118,15,2),(119,15,3),(120,15,4);
/*!40000 ALTER TABLE `ieeetags_node_filters` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ieeetags_node_parents`
--

DROP TABLE IF EXISTS `ieeetags_node_parents`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `ieeetags_node_parents` (
  `id` int(11) NOT NULL auto_increment,
  `from_node_id` int(11) NOT NULL,
  `to_node_id` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `from_node_id` (`from_node_id`,`to_node_id`),
  KEY `to_node_id_refs_id_304469d3` (`to_node_id`),
  CONSTRAINT `to_node_id_refs_id_304469d3` FOREIGN KEY (`to_node_id`) REFERENCES `ieeetags_node` (`id`),
  CONSTRAINT `from_node_id_refs_id_304469d3` FOREIGN KEY (`from_node_id`) REFERENCES `ieeetags_node` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=29 DEFAULT CHARSET=latin1;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `ieeetags_node_parents`
--

LOCK TABLES `ieeetags_node_parents` WRITE;
/*!40000 ALTER TABLE `ieeetags_node_parents` DISABLE KEYS */;
INSERT INTO `ieeetags_node_parents` VALUES (15,2,1),(16,3,1),(17,4,1),(18,5,1),(19,6,1),(20,7,1),(21,8,1),(22,9,1),(23,10,1),(24,11,1),(25,12,1),(26,13,1),(27,14,1),(28,15,1);
/*!40000 ALTER TABLE `ieeetags_node_parents` ENABLE KEYS */;
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
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `ieeetags_node_related_tags`
--

LOCK TABLES `ieeetags_node_related_tags` WRITE;
/*!40000 ALTER TABLE `ieeetags_node_related_tags` DISABLE KEYS */;
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
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `ieeetags_node_societies`
--

LOCK TABLES `ieeetags_node_societies` WRITE;
/*!40000 ALTER TABLE `ieeetags_node_societies` DISABLE KEYS */;
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
  `name` varchar(50) NOT NULL,
  PRIMARY KEY  (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=latin1;
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
  `permission_type` varchar(1000) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `ieeetags_permission_user_id` (`user_id`),
  KEY `ieeetags_permission_object_type_id` (`object_type_id`),
  CONSTRAINT `object_type_id_refs_id_618b7840` FOREIGN KEY (`object_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `user_id_refs_id_51c9aa44` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
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
  `role` varchar(1000) NOT NULL,
  `reset_key` varchar(1000) default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `user_id_refs_id_5285cb49` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=latin1;
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
  `ieee_id` varchar(500) default NULL,
  `name` varchar(500) NOT NULL,
  `description` varchar(1000) NOT NULL,
  `url` varchar(1000) NOT NULL,
  `year` int(11) default NULL,
  `standard_status` varchar(100) NOT NULL,
  `priority_to_tag` tinyint(1) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `ieeetags_resource_resource_type_id` (`resource_type_id`),
  CONSTRAINT `resource_type_id_refs_id_21a19251` FOREIGN KEY (`resource_type_id`) REFERENCES `ieeetags_resourcetype` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
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
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
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
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
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
  `name` varchar(50) NOT NULL,
  PRIMARY KEY  (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=latin1;
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
  `name` varchar(500) NOT NULL,
  `abbreviation` varchar(20) NOT NULL,
  `url` varchar(1000) NOT NULL,
  PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `ieeetags_society`
--

LOCK TABLES `ieeetags_society` WRITE;
/*!40000 ALTER TABLE `ieeetags_society` DISABLE KEYS */;
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
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `ieeetags_society_users`
--

LOCK TABLES `ieeetags_society_users` WRITE;
/*!40000 ALTER TABLE `ieeetags_society_users` DISABLE KEYS */;
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

-- Dump completed on 2009-04-09 22:40:10
