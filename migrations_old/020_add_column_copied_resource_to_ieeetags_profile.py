from dmigrations.mysql import migrations as m
import datetime
migration = m.AddColumn('ieeetags', 'profile', 'copied_resource', 'integer', 'ieeetags_resource')
