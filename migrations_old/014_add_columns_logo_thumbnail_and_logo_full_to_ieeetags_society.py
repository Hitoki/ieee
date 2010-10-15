from dmigrations.mysql import migrations as m
import datetime
migration = m.Compound([
    m.AddColumn('ieeetags', 'society', 'logo_thumbnail', 'varchar(100) NOT NULL'),
    m.AddColumn('ieeetags', 'society', 'logo_full', 'varchar(100) NOT NULL'),
])

