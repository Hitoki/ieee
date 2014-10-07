from dmigrations.mysql import migrations as m
import datetime
migration = m.AddColumn('ieeetags', 'profile', 'last_login_time', 'datetime NULL')
