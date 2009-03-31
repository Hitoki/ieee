from dmigrations.mysql import migrations as m
import datetime

migration001 = m.Migration(sql_up=["""
    CREATE TABLE `django_content_type` (
        `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
        `name` varchar(100) NOT NULL,
        `app_label` varchar(100) NOT NULL,
        `model` varchar(100) NOT NULL,
        UNIQUE (`app_label`, `model`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8
    ;
"""], sql_down=["""
    DROP TABLE `django_content_type`;
"""])

migration002 = m.Migration(sql_up=["""
    CREATE TABLE `auth_permission` (
        `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
        `name` varchar(50) NOT NULL,
        `content_type_id` integer NOT NULL,
        `codename` varchar(100) NOT NULL,
        UNIQUE (`content_type_id`, `codename`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8
    ;
""", """
    CREATE TABLE `auth_group` (
        `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
        `name` varchar(80) NOT NULL UNIQUE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8
    ;
""", """
    CREATE TABLE `auth_user` (
        `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
        `username` varchar(30) NOT NULL UNIQUE,
        `first_name` varchar(30) NOT NULL,
        `last_name` varchar(30) NOT NULL,
        `email` varchar(75) NOT NULL,
        `password` varchar(128) NOT NULL,
        `is_staff` bool NOT NULL,
        `is_active` bool NOT NULL,
        `is_superuser` bool NOT NULL,
        `last_login` datetime NOT NULL,
        `date_joined` datetime NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8
    ;
""", """
    CREATE TABLE `auth_message` (
        `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
        `user_id` integer NOT NULL,
        `message` longtext NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8
    ;
""", """
    ALTER TABLE `auth_message` ADD CONSTRAINT user_id_refs_id_650f49a6 FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
""", """
    CREATE TABLE `auth_group_permissions` (
        `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
        `group_id` integer NOT NULL,
        `permission_id` integer NOT NULL,
        UNIQUE (`group_id`, `permission_id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8
    ;
""", """
    ALTER TABLE `auth_group_permissions` ADD CONSTRAINT group_id_refs_id_3cea63fe FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`);
""", """
    ALTER TABLE `auth_group_permissions` ADD CONSTRAINT permission_id_refs_id_5886d21f FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`);
""", """
    CREATE TABLE `auth_user_groups` (
        `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
        `user_id` integer NOT NULL,
        `group_id` integer NOT NULL,
        UNIQUE (`user_id`, `group_id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8
    ;
""", """
    ALTER TABLE `auth_user_groups` ADD CONSTRAINT user_id_refs_id_7ceef80f FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
""", """
    ALTER TABLE `auth_user_groups` ADD CONSTRAINT group_id_refs_id_f116770 FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`);
""", """
    CREATE TABLE `auth_user_user_permissions` (
        `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
        `user_id` integer NOT NULL,
        `permission_id` integer NOT NULL,
        UNIQUE (`user_id`, `permission_id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8
    ;
""", """
    ALTER TABLE `auth_user_user_permissions` ADD CONSTRAINT user_id_refs_id_dfbab7d FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
""", """
    ALTER TABLE `auth_user_user_permissions` ADD CONSTRAINT permission_id_refs_id_67e79cb FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`);
""", """
    -- The following references should be added but depend on non-existent tables:
""", """
    -- ALTER TABLE `auth_permission` ADD CONSTRAINT content_type_id_refs_id_728de91f FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`);
"""], sql_down=["""
    DROP TABLE `auth_user_user_permissions`;
""", """
    DROP TABLE `auth_user_groups`;
""", """
    DROP TABLE `auth_group_permissions`;
""", """
    DROP TABLE `auth_message`;
""", """
    DROP TABLE `auth_user`;
""", """
    DROP TABLE `auth_group`;
""", """
    DROP TABLE `auth_permission`;
"""])

migration003 = m.Migration(sql_up=["""
    CREATE TABLE `django_session` (
        `session_key` varchar(40) NOT NULL PRIMARY KEY,
        `session_data` longtext NOT NULL,
        `expire_date` datetime NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8
    ;
"""], sql_down=["""
    DROP TABLE `django_session`;
"""])

migration004 = m.Migration(sql_up=["""
    CREATE TABLE `django_admin_log` (
        `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
        `action_time` datetime NOT NULL,
        `user_id` integer NOT NULL,
        `content_type_id` integer NULL,
        `object_id` longtext NULL,
        `object_repr` varchar(200) NOT NULL,
        `action_flag` smallint UNSIGNED NOT NULL,
        `change_message` longtext NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8
    ;
""", """
    -- The following references should be added but depend on non-existent tables:
""", """
    -- ALTER TABLE `django_admin_log` ADD CONSTRAINT user_id_refs_id_c8665aa FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
""", """
    -- ALTER TABLE `django_admin_log` ADD CONSTRAINT content_type_id_refs_id_288599e6 FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`);
"""], sql_down=["""
    DROP TABLE `django_admin_log`;
"""])

migration005 = m.Migration(sql_up=["""
    CREATE TABLE `django_site` (
        `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
        `domain` varchar(100) NOT NULL,
        `name` varchar(50) NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8
    ;
"""], sql_down=["""
    DROP TABLE `django_site`;
"""])

migration006 = m.Migration(sql_up=["""
    CREATE TABLE `ieeetags_nodetype` (
        `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
        `name` varchar(50) NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8
    ;
""", """
    CREATE TABLE `ieeetags_node` (
        `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
        `name` varchar(500) NOT NULL,
        `parent_id` integer NULL,
        `node_type_id` integer NOT NULL,
        `num_related_tags` integer NULL,
        `num_resources` integer NULL,
        `num_related_sectors` integer NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8
    ;
""", """
    ALTER TABLE `ieeetags_node` ADD CONSTRAINT node_type_id_refs_id_652d089 FOREIGN KEY (`node_type_id`) REFERENCES `ieeetags_nodetype` (`id`);
""", """
    ALTER TABLE `ieeetags_node` ADD CONSTRAINT parent_id_refs_id_aadfc7d FOREIGN KEY (`parent_id`) REFERENCES `ieeetags_node` (`id`);
""", """
    CREATE TABLE `ieeetags_society` (
        `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
        `name` varchar(500) NOT NULL,
        `abbreviation` varchar(20) NOT NULL,
        `url` varchar(1000) NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8
    ;
""", """
    CREATE TABLE `ieeetags_resourcetype` (
        `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
        `name` varchar(50) NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8
    ;
""", """
    CREATE TABLE `ieeetags_resource` (
        `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
        `resource_type_id` integer NOT NULL,
        `ieee_id` varchar(500) NULL,
        `name` varchar(500) NOT NULL,
        `description` varchar(1000) NOT NULL,
        `url` varchar(1000) NOT NULL,
        `year` integer NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8
    ;
""", """
    ALTER TABLE `ieeetags_resource` ADD CONSTRAINT resource_type_id_refs_id_21a19251 FOREIGN KEY (`resource_type_id`) REFERENCES `ieeetags_resourcetype` (`id`);
""", """
    CREATE TABLE `ieeetags_filter` (
        `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
        `name` varchar(50) NOT NULL,
        `value` varchar(500) NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8
    ;
""", """
    CREATE TABLE `ieeetags_permission` (
        `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
        `user_id` integer NOT NULL,
        `object_type_id` integer NOT NULL,
        `object_id` integer UNSIGNED NOT NULL,
        `permission_type` varchar(1000) NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8
    ;
""", """
    CREATE TABLE `ieeetags_profile` (
        `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
        `user_id` integer NOT NULL UNIQUE,
        `role` varchar(1000) NOT NULL,
        `reset_key` varchar(1000) NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8
    ;
""", """
    CREATE TABLE `ieeetags_node_societies` (
        `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
        `node_id` integer NOT NULL,
        `society_id` integer NOT NULL,
        UNIQUE (`node_id`, `society_id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8
    ;
""", """
    ALTER TABLE `ieeetags_node_societies` ADD CONSTRAINT node_id_refs_id_151b8f74 FOREIGN KEY (`node_id`) REFERENCES `ieeetags_node` (`id`);
""", """
    ALTER TABLE `ieeetags_node_societies` ADD CONSTRAINT society_id_refs_id_4283f3d1 FOREIGN KEY (`society_id`) REFERENCES `ieeetags_society` (`id`);
""", """
    CREATE TABLE `ieeetags_node_filters` (
        `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
        `node_id` integer NOT NULL,
        `filter_id` integer NOT NULL,
        UNIQUE (`node_id`, `filter_id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8
    ;
""", """
    ALTER TABLE `ieeetags_node_filters` ADD CONSTRAINT node_id_refs_id_2d5d995f FOREIGN KEY (`node_id`) REFERENCES `ieeetags_node` (`id`);
""", """
    ALTER TABLE `ieeetags_node_filters` ADD CONSTRAINT filter_id_refs_id_1340c915 FOREIGN KEY (`filter_id`) REFERENCES `ieeetags_filter` (`id`);
""", """
    CREATE TABLE `ieeetags_node_related_tags` (
        `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
        `from_node_id` integer NOT NULL,
        `to_node_id` integer NOT NULL,
        UNIQUE (`from_node_id`, `to_node_id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8
    ;
""", """
    ALTER TABLE `ieeetags_node_related_tags` ADD CONSTRAINT from_node_id_refs_id_3cec9c56 FOREIGN KEY (`from_node_id`) REFERENCES `ieeetags_node` (`id`);
""", """
    ALTER TABLE `ieeetags_node_related_tags` ADD CONSTRAINT to_node_id_refs_id_3cec9c56 FOREIGN KEY (`to_node_id`) REFERENCES `ieeetags_node` (`id`);
""", """
    CREATE TABLE `ieeetags_node_related_sectors` (
        `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
        `from_node_id` integer NOT NULL,
        `to_node_id` integer NOT NULL,
        UNIQUE (`from_node_id`, `to_node_id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8
    ;
""", """
    ALTER TABLE `ieeetags_node_related_sectors` ADD CONSTRAINT from_node_id_refs_id_747bba37 FOREIGN KEY (`from_node_id`) REFERENCES `ieeetags_node` (`id`);
""", """
    ALTER TABLE `ieeetags_node_related_sectors` ADD CONSTRAINT to_node_id_refs_id_747bba37 FOREIGN KEY (`to_node_id`) REFERENCES `ieeetags_node` (`id`);
""", """
    CREATE TABLE `ieeetags_society_users` (
        `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
        `society_id` integer NOT NULL,
        `user_id` integer NOT NULL,
        UNIQUE (`society_id`, `user_id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8
    ;
""", """
    ALTER TABLE `ieeetags_society_users` ADD CONSTRAINT society_id_refs_id_e1d6f1c FOREIGN KEY (`society_id`) REFERENCES `ieeetags_society` (`id`);
""", """
    ALTER TABLE `ieeetags_society_users` ADD CONSTRAINT user_id_refs_id_69d6ab23 FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
""", """
    CREATE TABLE `ieeetags_resource_nodes` (
        `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
        `resource_id` integer NOT NULL,
        `node_id` integer NOT NULL,
        UNIQUE (`resource_id`, `node_id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8
    ;
""", """
    ALTER TABLE `ieeetags_resource_nodes` ADD CONSTRAINT resource_id_refs_id_3c53589 FOREIGN KEY (`resource_id`) REFERENCES `ieeetags_resource` (`id`);
""", """
    ALTER TABLE `ieeetags_resource_nodes` ADD CONSTRAINT node_id_refs_id_4d52045f FOREIGN KEY (`node_id`) REFERENCES `ieeetags_node` (`id`);
""", """
    CREATE TABLE `ieeetags_resource_societies` (
        `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
        `resource_id` integer NOT NULL,
        `society_id` integer NOT NULL,
        UNIQUE (`resource_id`, `society_id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8
    ;
""", """
    ALTER TABLE `ieeetags_resource_societies` ADD CONSTRAINT resource_id_refs_id_2e9a7be4 FOREIGN KEY (`resource_id`) REFERENCES `ieeetags_resource` (`id`);
""", """
    ALTER TABLE `ieeetags_resource_societies` ADD CONSTRAINT society_id_refs_id_5593f5d1 FOREIGN KEY (`society_id`) REFERENCES `ieeetags_society` (`id`);
""", """
    -- The following references should be added but depend on non-existent tables:
""", """
    -- ALTER TABLE `ieeetags_permission` ADD CONSTRAINT user_id_refs_id_51c9aa44 FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
""", """
    -- ALTER TABLE `ieeetags_profile` ADD CONSTRAINT user_id_refs_id_5285cb49 FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
""", """
    -- ALTER TABLE `ieeetags_permission` ADD CONSTRAINT object_type_id_refs_id_618b7840 FOREIGN KEY (`object_type_id`) REFERENCES `django_content_type` (`id`);
"""], sql_down=["""
    DROP TABLE `ieeetags_resource_societies`;
""", """
    DROP TABLE `ieeetags_resource_nodes`;
""", """
    DROP TABLE `ieeetags_society_users`;
""", """
    DROP TABLE `ieeetags_node_related_sectors`;
""", """
    DROP TABLE `ieeetags_node_related_tags`;
""", """
    DROP TABLE `ieeetags_node_filters`;
""", """
    DROP TABLE `ieeetags_node_societies`;
""", """
    DROP TABLE `ieeetags_profile`;
""", """
    DROP TABLE `ieeetags_permission`;
""", """
    DROP TABLE `ieeetags_filter`;
""", """
    DROP TABLE `ieeetags_resource`;
""", """
    DROP TABLE `ieeetags_resourcetype`;
""", """
    DROP TABLE `ieeetags_society`;
""", """
    ALTER TABLE `ieeetags_node` DROP FOREIGN KEY parent_id_refs_id_aadfc7d;
""", """
    DROP TABLE `ieeetags_node`;
""", """
    DROP TABLE `ieeetags_nodetype`;
"""])

migration = m.Compound([
    migration001,
    migration002,
    migration003,
    migration004,
    migration005,
    migration006,
])