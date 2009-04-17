
drop_all_tables.py
@REM manage.py syncdb
@REM manage.py syncdb --noinput
manage.py dmigrate all
manage.py loaddata initial_data.json
