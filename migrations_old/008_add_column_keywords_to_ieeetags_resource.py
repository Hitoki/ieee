from dmigrations.mysql import migrations as m
import datetime
migration = m.AddColumn('ieeetags', 'resource', 'keywords', 'varchar(1000) NOT NULL')
