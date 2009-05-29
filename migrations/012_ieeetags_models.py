from dmigrations.mysql import migrations as m
import datetime
migration = m.Migration(sql_up=["""
    CREATE TABLE `ieeetags_failedloginlog` (
        `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
        `username` varchar(30) NOT NULL,
        `ip` varchar(16) NOT NULL,
        `disabled` bool NOT NULL,
        `date_created` datetime NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8
    ;
"""], sql_down=["""
    DROP TABLE `ieeetags_failedloginlog`;
"""])
