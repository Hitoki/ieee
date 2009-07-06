from dmigrations.mysql import migrations as m
import datetime
migration = m.Compound([
    m.DropColumn('ieeetags', 'node', 'num_related_tags', 'integer NULL'),
    m.DropColumn('ieeetags', 'node', 'num_resources', 'integer NULL'),
])

