
drop_all_tables.py
@REM manage.py syncdb
manage.py syncdb --noinput
@REM manage.py dmigrate all
manage.py loaddata data.json
@REM load < fixtures\data-full-no-create.sql
