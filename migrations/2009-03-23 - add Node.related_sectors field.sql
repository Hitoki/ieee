
CREATE TABLE `ieeetags_node_related_sectors` (
  `id` int(11) NOT NULL auto_increment,
  `from_node_id` int(11) NOT NULL,
  `to_node_id` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `from_node_id` (`from_node_id`,`to_node_id`),
  KEY `to_node_id_refs_id_747bba37` (`to_node_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci AUTO_INCREMENT=1 ;

ALTER TABLE `ieeetags_node_related_sectors`
  ADD CONSTRAINT `to_node_id_refs_id_747bba37` FOREIGN KEY (`to_node_id`) REFERENCES `ieeetags_node` (`id`),
  ADD CONSTRAINT `from_node_id_refs_id_747bba37` FOREIGN KEY (`from_node_id`) REFERENCES `ieeetags_node` (`id`);
