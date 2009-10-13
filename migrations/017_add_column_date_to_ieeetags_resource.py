from dmigrations.mysql import migrations as m
import datetime
migration = m.AddColumn('ieeetags', 'resource', 'date', 'date')
