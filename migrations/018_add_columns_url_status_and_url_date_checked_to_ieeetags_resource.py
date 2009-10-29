from dmigrations.mysql import migrations as m
import datetime
migration = m.Compound([
    m.AddColumn('ieeetags', 'resource', 'url_status', 'varchar(100) NOT NULL'),
    m.AddColumn('ieeetags', 'resource', 'url_date_checked', 'datetime'),
    m.AddColumn('ieeetags', 'resource', 'url_error', 'varchar(1000)'),
])

