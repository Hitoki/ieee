from dmigrations.mysql import migrations as m
import datetime
migration = m.Migration(sql_up=["""
    CREATE TABLE `ieeetags_urlcheckerlog` (
        `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
        `date_started` datetime NOT NULL,
        `date_ended` datetime,
        `date_updated` datetime NOT NULL,
        `status` varchar(1000) NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8
    ;
"""], sql_down=["""
    DROP TABLE `ieeetags_urlcheckerlog`;
"""])
