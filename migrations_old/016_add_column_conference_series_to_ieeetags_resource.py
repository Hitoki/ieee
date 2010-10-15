from dmigrations.mysql import migrations as m
import datetime
migration = m.AddColumn('ieeetags', 'resource', 'conference_series', 'varchar(100) NOT NULL')
